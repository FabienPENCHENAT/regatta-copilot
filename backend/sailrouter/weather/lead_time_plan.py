from __future__ import annotations

import math


class LeadTimePlan:
    """Which forecast lead times (hours after the cycle) exist and must be fetched for a time window.

    Deterministic GFS 0.25° on NOMADS is hourly up to f120, then 3-hourly up to f384. GEFS is 3-hourly
    from f000 (decision D6): build it with `hourly_until_h=0`.
    """

    def __init__(self, hourly_until_h: int = 120, coarse_step_h: int = 3, last_h: int = 384) -> None:
        self._hourly_until = hourly_until_h
        self._coarse_step = coarse_step_h
        self._last = last_h

    @classmethod
    def gefs(cls) -> LeadTimePlan:
        """GEFS 0.5° (`pgrb2a`): 3-hourly from f000 to f240."""
        return cls(hourly_until_h=0, coarse_step_h=3, last_h=240)

    def all_lead_hours(self) -> list[int]:
        hourly = list(range(0, self._hourly_until + 1))
        coarse_start = self._hourly_until + self._coarse_step
        return hourly + list(range(coarse_start, self._last + 1, self._coarse_step))

    def lead_hours_covering(self, first_h: float, last_h: float) -> list[int]:
        """Smallest list of lead times whose span contains [first_h, last_h] (bracketing both ends)."""
        if first_h < 0 or last_h > self._last or first_h > last_h:
            raise ValueError(f"window f{first_h:.1f}–f{last_h:.1f} outside the forecast (f000–f{self._last})")
        leads = self.all_lead_hours()
        below = [h for h in leads if h <= math.floor(first_h)]
        above = [h for h in leads if h >= math.ceil(last_h)]
        low, high = below[-1], above[0]
        return [h for h in leads if low <= h <= high]
