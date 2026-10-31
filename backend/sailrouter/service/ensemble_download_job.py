from __future__ import annotations

import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sailrouter.service.ensemble_status import DOWNLOADING, READY, UNAVAILABLE, EnsembleStatus
from sailrouter.weather.gefs_run_catalog import GefsRunCatalog
from sailrouter.weather.gefs_run_downloader import GefsRunDownloader, ProgressCallback
from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.nomads_client import DataNotAvailable
from sailrouter.weather.run_download_lock import RunDownloadLock


class EnsembleDownloadJob:
    """Downloads the GEFS run covering a routing window, at most one download at a time, and reports progress.

    `ensure` is called by every route request: it returns the newest run already on disk (or None) and starts
    a background download when a newer run should exist. The command line calls `download` directly. A run
    found incomplete on NOMADS, or a network failure, is not retried before `retry_after`.
    """

    def __init__(
        self, catalog: GefsRunCatalog, downloader: GefsRunDownloader, lock: RunDownloadLock,
        margin_h: float = 12.0, retry_after: timedelta = timedelta(minutes=10),
        now: Callable[[], datetime] = lambda: datetime.now(UTC), sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._catalog = catalog
        self._downloader = downloader
        self._lock = lock
        self._margin = timedelta(hours=margin_h)
        self._retry_after = retry_after
        self._now = now
        self._sleep = sleep
        self._mutex = threading.Lock()
        self._thread: threading.Thread | None = None
        self._window: tuple[datetime, datetime] | None = None
        self._run: ModelRun | None = None
        self._done = self._total = 0
        self._error: str | None = None
        self._failed_at: dict[str, datetime] = {}  # run key (or "network") → when it last failed

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def ensure(self, start: datetime, end: datetime) -> ModelRun | None:
        now = self._now()
        self._window = (start, end)
        ready = self._catalog.ready_run(start, end, now)
        latest = self._catalog.candidates(now)[0]
        if ready != latest and not self._recently_failed(latest.key, now) and not self._recently_failed("network", now):
            self.start(start, end)
        return ready

    def start(self, start: datetime, end: datetime) -> bool:
        with self._mutex:
            if self.is_running:
                return False
            self._window = (start, end)
            self._thread = threading.Thread(target=self._download_quietly, args=(start, end), daemon=True,
                                            name="gefs-download")
            self._thread.start()
            return True

    def wait(self, timeout_s: float | None = None) -> None:
        if self._thread is not None:
            self._thread.join(timeout_s)

    def status(self) -> EnsembleStatus:
        members = len(self._catalog.members)
        if self.is_running:
            return EnsembleStatus(DOWNLOADING, self._run, self._done, self._total, members)
        ready = self._catalog.ready_run(*self._window, self._now()) if self._window else None
        if ready is not None:
            _, total = self._catalog.files_on_disk(ready, *self._window)
            return EnsembleStatus(READY, ready, total, total, members)
        return EnsembleStatus(UNAVAILABLE, None, 0, 0, members, self._error)

    def download(self, start: datetime, end: datetime, on_progress: ProgressCallback | None = None) -> ModelRun | None:
        """Blocking: puts the newest complete candidate run on disk for the window and returns it (None when no
        candidate is complete on NOMADS)."""
        now = self._now()
        for run in self._catalog.candidates(now):
            leads = self._catalog.lead_hours(run, start, end + self._margin) or self._catalog.lead_hours(run, start, end)
            if not leads or self._recently_failed(run.key, now):
                continue
            self._run, self._error = run, None
            self._wait_for_other_process(run, start, end)
            try:
                self._lock.touch(run)
                self._downloader.download(run, leads, self._catalog.members, self._progress(run, on_progress))
            except DataNotAvailable:
                self._failed_at[run.key] = now
                continue
            finally:
                self._lock.release(run)
            return run
        return None

    def _download_quietly(self, start: datetime, end: datetime) -> None:
        try:
            if self.download(start, end) is None:
                self._error = "no complete GEFS run on NOMADS"
        except (ConnectionError, OSError) as error:
            self._error = str(error)
            self._failed_at["network"] = self._now()

    def _progress(self, run: ModelRun, forward: ProgressCallback | None) -> ProgressCallback:
        def update(done: int, total: int) -> None:
            self._done, self._total = done, total
            self._lock.touch(run)
            if forward:
                forward(done, total)

        return update

    def _wait_for_other_process(self, run: ModelRun, start: datetime, end: datetime) -> None:
        while self._lock.held_by_other(run):
            self._done, self._total = self._catalog.files_on_disk(run, start, end)
            self._sleep(5.0)

    def _recently_failed(self, key: str, now: datetime) -> bool:
        failed = self._failed_at.get(key)
        return failed is not None and now - failed < self._retry_after
