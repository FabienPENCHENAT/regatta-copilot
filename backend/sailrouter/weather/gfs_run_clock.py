from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sailrouter.weather.model_run import ModelRun

CYCLE_HOURS = 6


class GfsRunClock:
    """Knows the GFS/GEFS cycles (00/06/12/18 UTC) and when a run is expected to be complete on NOMADS.

    A run is assumed complete `availability_delay` after its cycle (about 4–5 h on NOMADS). The caller still
    checks availability and falls back to `previous` when the files are not there yet.
    """

    def __init__(self, model: str = "gfs", availability_delay: timedelta = timedelta(hours=5)) -> None:
        self._model = model
        self._delay = availability_delay

    def latest_complete(self, now: datetime) -> ModelRun:
        ready_cycle = now.astimezone(UTC) - self._delay
        hour = ready_cycle.hour - ready_cycle.hour % CYCLE_HOURS
        cycle = ready_cycle.replace(hour=hour, minute=0, second=0, microsecond=0)
        return ModelRun(self._model, cycle)

    def previous(self, run: ModelRun) -> ModelRun:
        return ModelRun(run.model, run.cycle - timedelta(hours=CYCLE_HOURS))

    def next_expected(self, run: ModelRun) -> datetime:
        """When the run after `run` should be complete."""
        return run.cycle + timedelta(hours=CYCLE_HOURS) + self._delay
