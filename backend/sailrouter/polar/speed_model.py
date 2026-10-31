from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from sailrouter.polar.boat_options import BoatOptions
from sailrouter.polar.vr_polar import VrPolar


class SpeedModel:
    """Polar × options → best allowed sail and boat speed, for many (TWS, TWA) at once.

    Speed = table speed of the best allowed sail × foil factor (if foils) × hull ratio (if hull)
    × global speed ratio. The VR auto-sail hysteresis (`autoSailChangeTolerance`) is ignored: the router
    always takes the fastest sail and pays the sail-change penalty.
    """

    def __init__(self, vr_polar: VrPolar, options: BoatOptions) -> None:
        self._vr = vr_polar
        self._options = options
        self._allowed = np.array([options.allows_sail(name) for name in vr_polar.polar.sail_names])
        if not self._allowed.any():
            raise ValueError("no sail allowed by these options")

    @property
    def sail_names(self) -> tuple[str, ...]:
        return self._vr.polar.sail_names

    def best(self, tws_kn: ArrayLike, twa_deg: ArrayLike) -> tuple[NDArray[np.int8], NDArray[np.float64]]:
        """Best sail index (into `sail_names`) and speed (kn). `twa_deg` may be signed."""
        twa_abs = np.abs(np.asarray(twa_deg, float))
        tws = np.asarray(tws_kn, float)
        speeds = self._vr.polar.speeds(tws, twa_abs)
        speeds[~self._allowed] = -1.0
        sail = np.argmax(speeds, axis=0).astype(np.int8)
        speed = np.take_along_axis(speeds, sail[None].astype(np.intp), axis=0)[0]
        return sail, speed * self._factor(tws, twa_abs)

    def _factor(self, tws: NDArray, twa_abs: NDArray) -> NDArray | float:
        factor: NDArray | float = self._vr.global_speed_ratio
        if self._options.hull:
            factor = factor * self._vr.hull_ratio
        if self._options.foil:
            factor = factor * self._vr.foil.factor(tws, twa_abs)
        return factor
