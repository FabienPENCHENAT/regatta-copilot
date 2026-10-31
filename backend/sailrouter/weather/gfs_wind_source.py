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
    The GEFS source of step 4 will return one `WindField` per member the same way.
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
        self, start: datetime, end: datetime, now: datetime, on_progress: ProgressCallback | None = None
    ) -> tuple[WindField, ModelRun]:
        run = self._clock.latest_complete(now)
        for _ in range(self._max_fallback_runs + 1):
            leads = self._plan.lead_hours_covering(run.hours_since_cycle(start), run.hours_since_cycle(end))
            try:
                self._downloader.download(run, leads, on_progress)
            except DataNotAvailable:
                run = self._clock.previous(run)
                continue
            grids = [self._decoder.decode(self._store.path(run, lead)) for lead in leads]
            return WindField(grids), run
        raise DataNotAvailable(f"no complete GFS run found on NOMADS up to {run.key}")
