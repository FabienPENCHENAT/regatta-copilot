from __future__ import annotations

from datetime import datetime

from sailrouter.weather.forecast_store import ForecastStore
from sailrouter.weather.gfs_run_clock import GfsRunClock
from sailrouter.weather.gfs_run_downloader import GfsRunDownloader, ProgressCallback
from sailrouter.weather.grib_decoder import GribDecoder
from sailrouter.weather.lead_time_plan import LeadTimePlan
from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.nomads_client import DataNotAvailable
from sailrouter.weather.wind_field import WindField


class GfsWindSource:
    """Gives the deterministic GFS `WindField` covering a time window, from the latest complete run.

    Falls back to older runs (up to `max_fallback_runs`) while the newest one is not complete on NOMADS.
    """

    def __init__(
        self,
        clock: GfsRunClock,
        plan: LeadTimePlan,
        downloader: GfsRunDownloader,
        store: ForecastStore,
        decoder: GribDecoder,
        max_fallback_runs: int = 2,
    ) -> None:
        self._clock = clock
        self._plan = plan
        self._downloader = downloader
        self._store = store
        self._decoder = decoder
        self._max_fallback_runs = max_fallback_runs

    def wind_field(
        self, start: datetime, end: datetime, now: datetime, on_progress: ProgressCallback | None = None,
        prefer_cached: bool = False,
    ) -> tuple[WindField, ModelRun]:
        """`prefer_cached`: use the newest run already on disk for the window rather than downloading a newer
        one (the web app, where the background refresher downloads); download only when none is on disk."""
        run = self.cached_run(start, end, now) if prefer_cached else None
        if run is None:
            run = self.download_latest(start, end, now, on_progress)
        grids = [self._decoder.decode(self._store.path(run, lead)) for lead in self._leads(run, start, end)]
        return WindField(grids), run

    def cached_run(self, start: datetime, end: datetime, now: datetime) -> ModelRun | None:
        """The newest candidate run (latest due, then older ones) whose lead times for the window are all on disk."""
        for run in self._candidates(now):
            if all(self._store.has(run, lead) for lead in self._leads(run, start, end)):
                return run
        return None

    def download_latest(
        self, start: datetime, end: datetime, now: datetime, on_progress: ProgressCallback | None = None,
    ) -> ModelRun:
        """Puts the newest complete run's lead times for the window on disk (nothing to do when cached)."""
        for run in self._candidates(now):
            try:
                self._downloader.download(run, self._leads(run, start, end), on_progress)
            except DataNotAvailable:
                continue
            return run
        raise DataNotAvailable(f"no complete GFS run found on NOMADS up to {self._clock.latest_complete(now).key}")

    def _candidates(self, now: datetime) -> list[ModelRun]:
        runs = [self._clock.latest_complete(now)]
        for _ in range(self._max_fallback_runs):
            runs.append(self._clock.previous(runs[-1]))
        return runs

    def _leads(self, run: ModelRun, start: datetime, end: datetime) -> list[int]:
        return self._plan.lead_hours_covering(run.hours_since_cycle(start), run.hours_since_cycle(end))
