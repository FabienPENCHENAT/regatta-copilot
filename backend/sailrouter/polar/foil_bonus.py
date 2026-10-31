from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray


@dataclass(frozen=True)
class FoilBonus:
    """Speed factor given by the foils option (VR polar `foil` block).

    Full bonus (`speed_ratio`, e.g. ×1.04) inside [twa_min, twa_max] × [tws_min, tws_max]; it fades linearly
    to none over `twa_merge` degrees / `tws_merge` knots outside those ranges. The two fades multiply
    (assumption: VR does not document how they combine).
    """

    speed_ratio: float
    twa_min: float
    twa_max: float
    twa_merge: float
    tws_min: float
    tws_max: float
    tws_merge: float

    def factor(self, tws_kn: ArrayLike, twa_abs_deg: ArrayLike) -> NDArray:
        twa_weight = _plateau(np.asarray(twa_abs_deg, float), self.twa_min, self.twa_max, self.twa_merge)
        tws_weight = _plateau(np.asarray(tws_kn, float), self.tws_min, self.tws_max, self.tws_merge)
        return 1.0 + (self.speed_ratio - 1.0) * twa_weight * tws_weight


def _plateau(values: NDArray, low: float, high: float, merge: float) -> NDArray:
    """1 inside [low, high], linear ramp to 0 over `merge` on each side, 0 beyond."""
    if merge <= 0:
        return ((values >= low) & (values <= high)).astype(float)
    rising = (values - (low - merge)) / merge
    falling = ((high + merge) - values) / merge
    return np.clip(np.minimum(rising, falling), 0.0, 1.0)
