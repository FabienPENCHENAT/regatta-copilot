from datetime import UTC, datetime

import pytest

from sailrouter.weather.forecast_store import ForecastStore
from sailrouter.weather.gefs_query_builder import GefsQueryBuilder
from sailrouter.weather.gefs_run_downloader import GefsRunDownloader
from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.nomads_client import DataNotAvailable
from sailrouter.weather.weather_area import WeatherArea

RUN = ModelRun("gefs", datetime(2026, 10, 31, 6, tzinfo=UTC))


class FakeNomads:
    def __init__(self, missing=()):
        self.requests = []
        self._missing = set(missing)

    def fetch_grib(self, script, params):
        self.requests.append(params["file"])
        if params["file"] in self._missing:
            raise DataNotAvailable(params["file"])
        return b"GRIB" + params["file"].encode()


def downloader(tmp_path, client):
    store = ForecastStore(tmp_path)
    return GefsRunDownloader(client, GefsQueryBuilder(WeatherArea()), store), store


def test_probes_the_last_lead_of_every_member_first_then_fills_the_rest(tmp_path):
    client = FakeNomads()
    gefs, store = downloader(tmp_path, client)
    progress = []
    assert gefs.download(RUN, [30, 33, 36], ["c00", "p01"], lambda d, t: progress.append((d, t))) == 6
    assert client.requests[:2] == ["gec00.t06z.pgrb2a.0p50.f036", "gep01.t06z.pgrb2a.0p50.f036"]
    assert store.has(RUN, 33, "p01") and store.path(RUN, 33, "p01").name == "f033-p01.grib2"
    assert progress[0] == (0, 6) and progress[-1] == (6, 6)


def test_resumes_where_it_stopped_and_counts_cached_files_as_done(tmp_path):
    client = FakeNomads()
    gefs, store = downloader(tmp_path, client)
    store.write(RUN, 30, b"GRIB", "c00")
    progress = []
    assert gefs.download(RUN, [30, 33], ["c00", "p01"], lambda d, t: progress.append((d, t))) == 3
    assert progress[0] == (1, 4)
    assert gefs.download(RUN, [30, 33], ["c00", "p01"]) == 0


def test_incomplete_run_fails_on_the_first_probe(tmp_path):
    client = FakeNomads(missing={"gep01.t06z.pgrb2a.0p50.f036"})
    gefs, _ = downloader(tmp_path, client)
    with pytest.raises(DataNotAvailable):
        gefs.download(RUN, [30, 33, 36], ["c00", "p01"])
    assert len(client.requests) == 2
