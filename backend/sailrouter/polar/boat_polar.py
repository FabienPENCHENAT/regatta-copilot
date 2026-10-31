from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


class BoatPolar:
    """Boat speed tables, one per sail, with a bilinear lookup on (TWS, |TWA|).

    `speeds_kn` is indexed `[sail, twa, tws]` like the VR `sail[].speed[twa][tws]` arrays. TWS and TWA
    outside the table axes are clamped to the first/last value.
    """

    def __init__(
        self, tws_kn: ArrayLike, twa_deg: ArrayLike, sail_names: tuple[str, ...], speeds_kn: ArrayLike
    ) -> None:
        self.tws_kn = np.asarray(tws_kn, dtype=float)
        self.twa_deg = np.asarray(twa_deg, dtype=float)
        self.sail_names = tuple(sail_names)
        self.speeds_kn = np.asarray(speeds_kn, dtype=float)
        expected = (len(self.sail_names), self.twa_deg.size, self.tws_kn.size)
        if self.speeds_kn.shape != expected:
            raise ValueError(f"speed table shape {self.speeds_kn.shape}, expected {expected}")
        for axis in (self.tws_kn, self.twa_deg):
            if axis.size < 2 or np.any(np.diff(axis) <= 0):
                raise ValueError("polar axes must be strictly increasing with at least 2 values")

    def speeds(self, tws_kn: ArrayLike, twa_abs_deg: ArrayLike) -> NDArray:
        """Speed of every sail: array of shape `(n_sails, *broadcast(tws, twa).shape)`."""
        tws, twa = np.broadcast_arrays(np.asarray(tws_kn, float), np.asarray(twa_abs_deg, float))
        i, fi = _bracket(self.twa_deg, twa)
        j, fj = _bracket(self.tws_kn, tws)
        table = self.speeds_kn
        low = table[:, i, j] * (1 - fj) + table[:, i, j + 1] * fj
        high = table[:, i + 1, j] * (1 - fj) + table[:, i + 1, j + 1] * fj
        return low * (1 - fi) + high * fi


def _bracket(axis: NDArray, values: NDArray) -> tuple[NDArray, NDArray]:
    """Lower index and fraction of each value on `axis` (clamped to the axis range)."""
    clamped = np.clip(values, axis[0], axis[-1])
    index = np.clip(np.searchsorted(axis, clamped, side="right") - 1, 0, axis.size - 2)
    fraction = (clamped - axis[index]) / (axis[index + 1] - axis[index])
    return index, fraction
