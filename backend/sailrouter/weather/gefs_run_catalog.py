from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sailrouter.weather.forecast_store import ForecastStore
from sailrouter.weather.gfs_run_clock import GfsRunClock
from sailrouter.weather.lead_time_plan import LeadTimePlan
from sailrouter.weather.model_run import ModelRun


class GefsRunCatalog:
    """Which GEFS runs may serve a time window, which lead times that needs, and how much of it is on disk.

    Candidates are the newest run the clock deems complete, then up to `max_fallback_runs` older ones
    (a run may be late on NOMADS). GEFS 0.5° is 3-hourly up to f240 (decision D6).
    """

    def __init__(
        self, clock: GfsRunClock, store: ForecastStore, members: Sequence[str],
        plan: LeadTimePlan | None = None, max_fallback_runs: int = 2,
    ) -> None:
        self._clock = clock
        self._store = store
        self.members = tuple(members)
        self._plan = plan or LeadTimePlan.gefs()
        self._max_fallback_runs = max_fallback_runs

    def candidates(self, now: datetime) -> list[ModelRun]:
        runs = [self._clock.latest_complete(now)]
        for _ in range(self._max_fallback_runs):
            runs.append(self._clock.previous(runs[-1]))
        return runs

    def lead_hours(self, run: ModelRun, start: datetime, end: datetime) -> list[int]:
        """Lead times bracketing [start, end]; empty when the window is outside this run's forecast."""
        try:
            return self._plan.lead_hours_covering(run.hours_since_cycle(start), run.hours_since_cycle(end))
        except ValueError:
            return []

    def files_on_disk(self, run: ModelRun, start: datetime, end: datetime) -> tuple[int, int]:
        """(files present, files needed) for every member over the window."""
        leads = self.lead_hours(run, start, end)
        total = len(leads) * len(self.members)
        return total - len(self._store.missing(run, leads, self.members)), total

    def is_complete(self, run: ModelRun, start: datetime, end: datetime) -> bool:
        done, total = self.files_on_disk(run, start, end)
        return total > 0 and done == total

    def ready_run(self, start: datetime, end: datetime, now: datetime) -> ModelRun | None:
        """The newest candidate run fully on disk for the window, if any."""
        return next((run for run in self.candidates(now) if self.is_complete(run, start, end)), None)
