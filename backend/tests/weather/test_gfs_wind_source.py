from datetime import UTC, datetime, timedelta

import numpy as np

from sailrouter.weather.forecast_store import ForecastStore
from sailrouter.weather.gfs_query_builder import GfsQueryBuilder
from sailrouter.weather.gfs_run_clock import GfsRunClock
from sailrouter.weather.gfs_run_downloader import GfsRunDownloader
from sailrouter.weather.gfs_wind_source import GfsWindSource
from sailrouter.weather.lead_time_plan import LeadTimePlan
from sailrouter.weather.nomads_client import DataNotAvailable
from sailrouter.weather.weather_area import WeatherArea
from sailrouter.weather.wind_grid import WindGrid

NOW = datetime(2026, 10, 31, 17, 30, tzinfo=UTC)  # 12z should be complete, but is not on the fake server


class FakeNomads:
    def __init__(self):
        self.requests = []

    def fetch_grib(self, script, params):
        self.requests.append(params["file"])
        if params["dir"].endswith("/12/atmos"):
            raise DataNotAvailable(params["file"])
        return b"GRIB" + params["file"].encode()


class FakeDecoder:
    def decode(self, path):
        content = path.read_bytes().decode(errors="ignore")
        cycle_hour, lead = int(content.split(".t")[1][:2]), int(content.split(".f")[1])
        valid = datetime(2026, 10, 31, cycle_hour, tzinfo=UTC) + timedelta(hours=lead)
        axis = np.array([0.0, 1.0])
        return WindGrid(valid, axis, axis, np.zeros((2, 2), np.float32), np.ones((2, 2), np.float32))


def make_source(tmp_path, client):
    store = ForecastStore(tmp_path)
    downloader = GfsRunDownloader(client, GfsQueryBuilder(WeatherArea()), store)
    return GfsWindSource(GfsRunClock(), LeadTimePlan(), downloader, store, FakeDecoder())


def test_falls_back_to_previous_run_and_caches(tmp_path):
    client = FakeNomads()
    start = datetime(2026, 11, 1, 12, 2, tzinfo=UTC)
    field, run = make_source(tmp_path, client).wind_field(start, start + timedelta(hours=3), NOW)
    assert run.key == "gfs-2026103106"
    assert client.requests[0] == "gfs.t12z.pgrb2.0p25.f028"  # probe: last lead of the newest run
    assert client.requests[1] == "gfs.t06z.pgrb2.0p25.f034"  # then the last lead of the previous run
    assert field.first_time == datetime(2026, 11, 1, 12, tzinfo=UTC)
    assert field.last_time == datetime(2026, 11, 1, 16, tzinfo=UTC)
    downloaded = len(client.requests)
    make_source(tmp_path, client).wind_field(start, start + timedelta(hours=3), NOW)
    assert len(client.requests) == downloaded + 1  # only the 12z probe again; 06z is cached


def test_prefer_cached_routes_on_the_run_on_disk_without_asking_nomads(tmp_path):
    start = datetime(2026, 11, 1, 12, 2, tzinfo=UTC)
    end = start + timedelta(hours=3)
    make_source(tmp_path, FakeNomads()).wind_field(start, end, NOW)  # puts 06z on disk
    offline = FakeNomads()
    source = make_source(tmp_path, offline)
    assert source.cached_run(start, end, NOW).key == "gfs-2026103106"
    _, run = source.wind_field(start, end, NOW, prefer_cached=True)
    assert run.key == "gfs-2026103106" and offline.requests == []
    assert source.cached_run(start, end + timedelta(hours=3), NOW) is None  # longer window: leads missing


def test_download_latest_only_downloads(tmp_path):
    start = datetime(2026, 11, 1, 12, 2, tzinfo=UTC)
    client = FakeNomads()
    run = make_source(tmp_path, client).download_latest(start, start + timedelta(hours=3), NOW)
    assert run.key == "gfs-2026103106" and len(client.requests) == 1 + 5  # 12z probe, then 06z f030..f034


def test_the_first_hours_come_from_the_previous_run_as_in_the_game(tmp_path):
    start = datetime(2026, 10, 31, 13, 0, tzinfo=UTC)  # 06z +7 h: before its +9 h, the game still has 00z
    client = FakeNomads()
    source = make_source(tmp_path, client)
    field, run = source.wind_field(start, start + timedelta(hours=3), now=start)
    assert run.key == "gfs-2026103106"
    assert sorted(client.requests[-2:]) == ["gfs.t00z.pgrb2.0p25.f013", "gfs.t00z.pgrb2.0p25.f014"]
    assert "gfs.t06z.pgrb2.0p25.f007" not in client.requests
    assert field.first_time == start and field.last_time == start + timedelta(hours=3)
    assert source.cached_run(start, start + timedelta(hours=3), start) == run
