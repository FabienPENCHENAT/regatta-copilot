from __future__ import annotations

from datetime import datetime, timedelta

from sailrouter.weather.lead_time_plan import LeadTimePlan
from sailrouter.weather.model_run import ModelRun

NEW_RUN_FROM_H = 9  # a run supplies the game's forecast times from 9 h after its cycle (decision D64)
CYCLE = timedelta(hours=6)


class GameRunMix:
    """Which GFS run supplies each forecast time of the game's weather, given the newest run the game has.

    Virtual Regatta does not swap runs at once: a new run supplies the forecast times from `NEW_RUN_FROM_H` after
    its cycle on, the earlier ones keep the previous run's. Run 06Z: 12:00 UTC still comes from 00Z (f012),
    15:00 from 06Z (f009), so the wind between them blends two runs (the logbook's blue/green gauge).
    """

    def __init__(self, plan: LeadTimePlan, new_run_from_h: float = NEW_RUN_FROM_H) -> None:
        self._plan = plan
        self._new_run_from_h = new_run_from_h

    def steps(self, newest: ModelRun, start: datetime, end: datetime) -> list[tuple[ModelRun, int]]:
        """(run, lead hour) of every forecast time covering [start, end], in time order."""
        leads = self._plan.lead_hours_covering(newest.hours_since_cycle(start), newest.hours_since_cycle(end))
        return [self._source(newest, lead) for lead in leads]

    def _source(self, run: ModelRun, lead: int) -> tuple[ModelRun, int]:
        while lead < self._new_run_from_h:
            run, lead = ModelRun(run.model, run.cycle - CYCLE), lead + int(CYCLE / timedelta(hours=1))
        return run, lead
