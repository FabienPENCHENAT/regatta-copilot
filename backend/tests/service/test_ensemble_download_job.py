import threading
from datetime import UTC, datetime, timedelta

from sailrouter.service.ensemble_download_job import EnsembleDownloadJob
from sailrouter.weather.forecast_store import ForecastStore
from sailrouter.weather.gefs_query_builder import GefsQueryBuilder
from sailrouter.weather.gefs_run_catalog import GefsRunCatalog
from sailrouter.weather.gefs_run_downloader import GefsRunDownloader
from sailrouter.weather.gfs_run_clock import GfsRunClock
from sailrouter.weather.nomads_client import DataNotAvailable
from sailrouter.weather.run_download_lock import RunDownloadLock
from sailrouter.weather.weather_area import WeatherArea

NOW = datetime(2026, 10, 31, 17, 30, tzinfo=UTC)  # 12z is due, 06z is the fallback
START = datetime(2026, 11, 1, 12, 2, tzinfo=UTC)
END = START + timedelta(hours=6)
MEMBERS = ("c00", "p01")


class FakeNomads:
    """Serves every file except those of `missing_cycle`; can hold the n-th request until released."""

    def __init__(self, missing_cycle="", hold_at=None, error=None):
        self.requests = []
        self.missing_cycle, self.hold_at, self.error = missing_cycle, hold_at, error
        self.reached, self.release = threading.Event(), threading.Event()

    def fetch_grib(self, script, params):
        self.requests.append(params["file"])
        if self.error:
            raise self.error
        if len(self.requests) == self.hold_at:
            self.reached.set()
            self.release.wait(5)
        if f".t{self.missing_cycle}z." in params["file"]:
            raise DataNotAvailable(params["file"])
        return b"GRIB"


def make_job(tmp_path, client, now=NOW):
    store = ForecastStore(tmp_path)
    catalog = GefsRunCatalog(GfsRunClock(model="gefs"), store, MEMBERS)
    downloader = GefsRunDownloader(client, GefsQueryBuilder(WeatherArea()), store)
    clock = {"now": now}
    job = EnsembleDownloadJob(catalog, downloader, RunDownloadLock(tmp_path), now=lambda: clock["now"],
                              sleep=lambda s: None)
    return job, clock


def test_nothing_on_disk_starts_a_background_download_then_reports_ready(tmp_path):
    client = FakeNomads(hold_at=3)
    job, _ = make_job(tmp_path, client)
    assert job.status().state == "unavailable"
    assert job.ensure(START, END) is None  # the request is served from GFS meanwhile
    assert client.reached.wait(5)
    status = job.status()
    assert (status.state, status.run.key, status.done, status.member_count) == ("downloading", "gefs-2026103112", 2, 2)
    assert status.total == 2 * 8  # f024..f045 (window + 12 h margin, bracketed) = 8 leads × 2 members
    client.release.set()
    job.wait(5)
    status = job.status()
    assert (status.state, status.run.key, status.done, status.total) == ("ready", "gefs-2026103112", 8, 8)  # f024..f033
    assert job.ensure(START, END).key == "gefs-2026103112"
    assert not job.is_running


def test_falls_back_to_the_previous_run_and_does_not_retry_the_late_one_at_once(tmp_path):
    client = FakeNomads(missing_cycle="12")
    job, clock = make_job(tmp_path, client)
    job.ensure(START, END)
    job.wait(5)
    assert job.status().run.key == "gefs-2026103106"
    requests = len(client.requests)
    assert job.ensure(START, END).key == "gefs-2026103106"
    assert not job.is_running and len(client.requests) == requests
    clock["now"] = NOW + timedelta(minutes=11)
    job.ensure(START, END)
    job.wait(5)
    assert len(client.requests) == requests + 1  # one probe of the late run, the old one is on disk


def test_network_failure_reports_unavailable_with_the_error(tmp_path):
    job, _ = make_job(tmp_path, FakeNomads(error=ConnectionError("NOMADS unreachable")))
    job.ensure(START, END)
    job.wait(5)
    status = job.status()
    assert status.state == "unavailable" and status.run is None and "unreachable" in status.error


def test_blocking_download_returns_the_run_for_the_command_line(tmp_path):
    progress = []
    job, _ = make_job(tmp_path, FakeNomads())
    run = job.download(START, END, lambda done, total: progress.append(done))
    assert run.key == "gefs-2026103112" and progress[-1] == 16
    assert not (tmp_path / "gefs-2026103112.downloading").exists()
