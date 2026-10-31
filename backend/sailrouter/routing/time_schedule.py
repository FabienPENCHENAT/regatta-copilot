from __future__ import annotations

from datetime import datetime, timedelta

# (until hour, step in hours): fine where the player types orders now, coarser where the forecast is less sure.
DEFAULT_PHASES = ((6.0, 0.25), (24.0, 0.5), (48.0, 1.0), (float("inf"), 3.0))


class TimeSchedule:
    """Routing time steps from `start` to `start + horizon_h`, by phases of (until hour, step): by default
    15 min until +6 h, 30 min until +24 h, 1 h until +48 h, then 3 h. A change of orders can therefore fall on
    any quarter of an hour at first. The last step is shortened to end exactly at the horizon."""

    def __init__(
        self, start: datetime, horizon_h: float, phases: tuple[tuple[float, float], ...] = DEFAULT_PHASES,
    ) -> None:
        if horizon_h <= 0:
            raise ValueError("horizon must be positive")
        if not phases or any(step <= 0 for _, step in phases):
            raise ValueError("phases need positive steps")
        self.start = start
        self.horizon_h = horizon_h
        self._phases = phases

    def elapsed_hours(self) -> list[float]:
        """Hours after `start` of every isochrone, starting with 0."""
        hours = [0.0]
        while hours[-1] < self.horizon_h - 1e-9:
            hours.append(min(hours[-1] + self._step_after(hours[-1]), self.horizon_h))
        return hours

    def times(self) -> list[datetime]:
        return [self.start + timedelta(hours=h) for h in self.elapsed_hours()]

    @property
    def end(self) -> datetime:
        return self.start + timedelta(hours=self.horizon_h)

    def _step_after(self, hour: float) -> float:
        return next(step for until, step in self._phases if hour < until - 1e-9)
