from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from sailrouter.polar.winch_timings import WinchTimings


class ManeuverPenalty:
    """Time lost (seconds of full-speed sailing) on a tack, a gybe or a sail change.

    V1 model: a maneuver makes the boat sail at `ratio` × speed during `timer`, so it loses
    `timer × (1 − ratio)` seconds. Timer and ratio come from the polar `winch` block (pro or std winch),
    interpolated linearly between the light-wind (`lws`, 10 kn) and heavy-wind (`hws`, 30 kn) values.
    `fixed_loss_s` overrides the loss of a maneuver with a constant (e.g. `{"tack": 60}`).
    A tack or gybe combined with a sail change costs the larger of the two (assumption: VR timers overlap).
    """

    def __init__(
        self, winch: WinchTimings, pro_winch: bool = True, fixed_loss_s: dict[str, float] | None = None
    ) -> None:
        self._winch = winch
        self._level = "pro" if pro_winch else "std"
        self._fixed = dict(fixed_loss_s or {})

    def loss_for(self, maneuver: str, tws_kn: ArrayLike) -> NDArray:
        """Seconds lost by one `maneuver` (`tack`, `gybe`, `sailChange`) at the given wind speeds."""
        tws = np.asarray(tws_kn, float)
        if maneuver in self._fixed:
            return np.full(tws.shape, float(self._fixed[maneuver]))
        timing = self._winch.timing(maneuver, self._level)
        span = self._winch.heavy_wind_kn - self._winch.light_wind_kn
        heavy = np.clip((tws - self._winch.light_wind_kn) / span, 0.0, 1.0)
        timer = timing.light_timer_s + (timing.heavy_timer_s - timing.light_timer_s) * heavy
        ratio = timing.light_ratio + (timing.heavy_ratio - timing.light_ratio) * heavy
        return timer * (1.0 - ratio)

    def loss_s(
        self,
        previous_twa_deg: ArrayLike,
        previous_sail: ArrayLike,
        twa_deg: ArrayLike,
        sail: ArrayLike,
        tws_kn: ArrayLike,
    ) -> NDArray:
        """Seconds lost between a previous state and a new one (arrays broadcast together).

        A NaN previous TWA (or a negative previous sail) means "unknown", e.g. at the start: no penalty.
        """
        prev_twa, new_twa = np.asarray(previous_twa_deg, float), np.asarray(twa_deg, float)
        prev_sail, new_sail = np.asarray(previous_sail), np.asarray(sail)
        switched_side = np.isfinite(prev_twa) & (np.sign(prev_twa) * np.sign(new_twa) < 0)
        through_wind = np.abs(prev_twa) + np.abs(new_twa) < 180.0
        tack = switched_side & through_wind
        gybe = switched_side & ~through_wind
        sail_change = (prev_sail >= 0) & (prev_sail != new_sail)
        tws = np.asarray(tws_kn, float)
        side_loss = np.where(tack, self.loss_for("tack", tws), 0.0)
        side_loss = np.where(gybe, self.loss_for("gybe", tws), side_loss)
        sail_loss = np.where(sail_change, self.loss_for("sailChange", tws), 0.0)
        return np.maximum(side_loss, sail_loss)
