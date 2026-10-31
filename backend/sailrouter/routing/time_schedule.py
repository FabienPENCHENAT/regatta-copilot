from __future__ import annotations

from datetime import datetime, timedelta


class TimeSchedule:
    """Routing time steps from `start` to `start + horizon_h`: `fine_step_h` until `fine_until_h`,
    `coarse_step_h` after (default 1 h until +24 h, then 3 h). The last step is shortened to end exactly
    at the horizon."""

    def __init__(
        self,
        start: datetime,
        horizon_h: float,
        fine_step_h: float = 1.0,
        fine_until_h: float = 24.0,
        coarse_step_h: float = 3.0,
    ) -> None:
        if horizon_h <= 0:
            raise ValueError("horizon must be positive")
        self.start = start
        self.horizon_h = horizon_h
        self._fine_step_h = fine_step_h
        self._fine_until_h = fine_until_h
        self._coarse_step_h = coarse_step_h

    def elapsed_hours(self) -> list[float]:
        """Hours after `start` of every isochrone, starting with 0."""
        hours = [0.0]
        while hours[-1] < self.horizon_h - 1e-9:
            step = self._fine_step_h if hours[-1] < self._fine_until_h - 1e-9 else self._coarse_step_h
            hours.append(min(hours[-1] + step, self.horizon_h))
        return hours

    def times(self) -> list[datetime]:
        return [self.start + timedelta(hours=h) for h in self.elapsed_hours()]

    @property
    def end(self) -> datetime:
        return self.start + timedelta(hours=self.horizon_h)
