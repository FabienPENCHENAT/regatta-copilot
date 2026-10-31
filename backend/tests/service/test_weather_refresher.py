import threading
from datetime import UTC, datetime, timedelta

from sailrouter.service.weather_refresher import WeatherRefresher
from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.nomads_client import DataNotAvailable

NOW = datetime(2026, 11, 1, 17, 30, tzinfo=UTC)
GFS_06, GFS_12 = (ModelRun("gfs", datetime(2026, 11, 1, h, tzinfo=UTC)) for h in (6, 12))
GEFS_06, GEFS_12 = (ModelRun("gefs", datetime(2026, 11, 1, h, tzinfo=UTC)) for h in (6, 12))


class FakeGfs:
    """`on_disk` is the newest run cached; `on_nomads` the newest run NOMADS serves (None: network down)."""

    def __init__(self, on_disk, on_nomads):
        self.on_disk, self.on_nomads, self.downloads = on_disk, on_nomads, []

    def cached_run(self, start, end, now):
        return self.on_disk

    def download_latest(self, start, end, now):
        if self.on_nomads is None:
            raise ConnectionError("NOMADS unreachable")
        if self.on_nomads != self.on_disk:
            self.downloads.append((self.on_nomads.key, start, end))
            self.on_disk = self.on_nomads
        return self.on_disk


class FakeEnsemble:
    def __init__(self, ready):
        self.ready, self.windows = ready, []

    def ensure(self, start, end):
        self.windows.append((start, end))
        return self.ready


class FakePrecompute:
    def __init__(self):
        self.calls = []

    def __call__(self, weather_changed):
        self.calls.append(weather_changed)
        return weather_changed


def make(gfs, gefs, window=(NOW, NOW + timedelta(hours=120))):
    precompute = FakePrecompute()
    return WeatherRefresher(gfs, gefs, lambda now: window, precompute, now=lambda: NOW), precompute


def test_downloads_the_new_gfs_run_for_the_window_plus_margin_and_precomputes():
    gfs, gefs = FakeGfs(GFS_06, GFS_12), FakeEnsemble(GEFS_06)
    refresher, precompute = make(gfs, gefs)
    outcome = refresher.run_once()
    assert outcome.gfs_downloaded and outcome.gfs_run == GFS_12 and outcome.precomputed
    assert gfs.downloads == [("gfs-2026110112", NOW, NOW + timedelta(hours=132))]
    assert gefs.windows == [(NOW, NOW + timedelta(hours=120))]
    assert precompute.calls == [True]


def test_nothing_new_means_no_download_and_no_forced_precompute():
    gfs, gefs = FakeGfs(GFS_12, GFS_12), FakeEnsemble(GEFS_06)
    refresher, precompute = make(gfs, gefs)
    refresher.run_once()  # first cycle after start-up: always precomputes
    outcome = refresher.run_once()
    assert not outcome.gfs_downloaded and not outcome.weather_changed and gfs.downloads == []
    assert precompute.calls == [True, False]


def test_a_new_gefs_run_on_disk_triggers_a_precompute():
    gfs, gefs = FakeGfs(GFS_12, GFS_12), FakeEnsemble(GEFS_06)
    refresher, precompute = make(gfs, gefs)
    refresher.run_once()
    gefs.ready = GEFS_12  # the background GEFS download finished
    outcome = refresher.run_once()
    assert outcome.weather_changed and outcome.gefs_run == GEFS_12
    assert precompute.calls == [True, True]


def test_network_failure_keeps_the_run_on_disk_and_still_asks_for_the_ensemble():
    gfs, gefs = FakeGfs(GFS_06, None), FakeEnsemble(None)
    refresher, _ = make(gfs, gefs)
    outcome = refresher.run_once()
    assert outcome.gfs_run == GFS_06 and not outcome.gfs_downloaded and len(gefs.windows) == 1


def test_incomplete_run_on_nomads_is_not_an_error():
    class Incomplete(FakeGfs):
        def download_latest(self, start, end, now):
            raise DataNotAvailable("f132 missing")

    refresher, _ = make(Incomplete(GFS_06, GFS_12), FakeEnsemble(None))
    assert refresher.run_once().gfs_run == GFS_06


def test_a_failed_precompute_is_retried_at_the_next_cycle():
    calls = []

    def flaky(changed):
        calls.append(changed)
        if len(calls) == 1:
            raise RuntimeError("boom")
        return True

    refresher = WeatherRefresher(FakeGfs(GFS_12, GFS_12), FakeEnsemble(GEFS_12), lambda now: (NOW, NOW), flaky,
                                 now=lambda: NOW)
    try:
        refresher.run_once()
    except RuntimeError:
        pass
    refresher.run_once()
    assert calls == [True, True]


def test_no_race_means_nothing_to_do():
    gfs = FakeGfs(None, GFS_12)
    refresher, precompute = make(gfs, FakeEnsemble(None), window=None)
    refresher._window = lambda now: None
    assert refresher.run_once().gfs_run is None and gfs.downloads == [] and precompute.calls == []


def test_thread_runs_a_cycle_at_once_then_stops():
    ran = threading.Event()

    def precompute(changed):
        ran.set()
        return True

    refresher = WeatherRefresher(FakeGfs(GFS_12, GFS_12), FakeEnsemble(None), lambda now: (NOW, NOW), precompute,
                                 now=lambda: NOW)
    refresher.start()
    assert ran.wait(5)
    refresher.stop(timeout_s=5)
    assert not refresher._thread.is_alive()
