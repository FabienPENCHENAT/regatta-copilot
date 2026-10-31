from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sailrouter.weather.model_run import ModelRun

CYCLE_HOURS = 6
GFS_DELAY = timedelta(hours=3, minutes=40)  # first lead times on NOMADS; the game switches about then (D45)
GEFS_DELAY = timedelta(hours=5)  # the ensemble is published later


class GfsRunClock:
    """Knows the GFS/GEFS cycles (00/06/12/18 UTC) and when a run is expected to be complete on NOMADS.

    A run is assumed usable `availability_delay` after its cycle (GFS ≈ 3 h 40, GEFS ≈ 5 h on NOMADS). The
    caller still checks availability and falls back to `previous` when the files are not all there yet.
    """

    def __init__(self, model: str = "gfs", availability_delay: timedelta | None = None) -> None:
        self._model = model
        self._delay = availability_delay or (GEFS_DELAY if model == "gefs" else GFS_DELAY)

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
