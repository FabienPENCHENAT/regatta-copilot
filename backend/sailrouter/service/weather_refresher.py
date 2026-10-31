from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.nomads_client import DataNotAvailable

log = logging.getLogger(__name__)
Window = tuple[datetime, datetime]


class GfsRunSource(Protocol):
    def cached_run(self, start: datetime, end: datetime, now: datetime) -> ModelRun | None: ...
    def download_latest(self, start: datetime, end: datetime, now: datetime) -> ModelRun: ...


class EnsembleRunSource(Protocol):
    def ensure(self, start: datetime, end: datetime) -> ModelRun | None: ...


@dataclass(frozen=True)
class RefreshOutcome:
    """What one refresh cycle did."""

    gfs_run: ModelRun | None
    gefs_run: ModelRun | None
    gfs_downloaded: bool
    weather_changed: bool
    precomputed: bool


class WeatherRefresher:
    """Keeps the weather fresh in the background so that route requests never wait for a download.

    Every `interval` (in a daemon thread, until `stop`): puts the latest complete GFS run for the route window
    (+ `margin`, as the window slides) on disk, lets the GEFS job start its background download when a newer run
    is due, then calls `precompute(weather_changed)` (weather changed = a GFS or GEFS run different from the
    previous cycle, always true on the first cycle).
    """

    def __init__(
        self, gfs: GfsRunSource, ensemble: EnsembleRunSource, window: Callable[[datetime], Window | None],
        precompute: Callable[[bool], bool], interval: timedelta = timedelta(minutes=10),
        margin: timedelta = timedelta(hours=12), now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._gfs = gfs
        self._ensemble = ensemble
        self._window = window
        self._precompute = precompute
        self._interval = interval
        self._margin = margin
        self._now = now
        self._weather: tuple[str | None, str | None] | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def run_once(self) -> RefreshOutcome:
        now = self._now()
        window = self._window(now)
        if window is None:
            return RefreshOutcome(None, None, False, False, False)
        start, end = window
        before = self._gfs.cached_run(start, end + self._margin, now)
        gfs_run = self._download_gfs(start, end + self._margin, now) or before
        gefs_run = self._ensemble.ensure(start, end)
        weather = (gfs_run.key if gfs_run else None, gefs_run.key if gefs_run else None)
        downloaded = gfs_run is not None and gfs_run != before
        if downloaded:
            log.info("GFS run %s downloaded for %s – %s", gfs_run.key, start.isoformat(), end.isoformat())
        changed = weather != self._weather
        if changed:
            log.info("weather for routing: GFS %s, GEFS %s", *weather)
        precomputed = self._precompute(changed)
        self._weather = weather  # only once pre-computed: a failure is retried at the next cycle
        return RefreshOutcome(gfs_run, gefs_run, downloaded, changed, precomputed)

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="weather-refresher")
        self._thread.start()
        log.info("weather refresher started (every %d min)", self._interval.total_seconds() // 60)

    def stop(self, timeout_s: float | None = 5.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout_s)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.run_once()
            except Exception:  # noqa: BLE001 - the refresher must survive any failure and try again later
                log.exception("weather refresh failed; next try in %s", self._interval)
            self._stop.wait(self._interval.total_seconds())

    def _download_gfs(self, start: datetime, end: datetime, now: datetime) -> ModelRun | None:
        try:
            run = self._gfs.download_latest(start, end, now)
        except (DataNotAvailable, ConnectionError, OSError) as error:
            log.warning("GFS download failed (%s); requests keep the run on disk", error)
            return None
        return run
