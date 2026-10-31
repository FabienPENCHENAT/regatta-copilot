from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import numpy as np
from numpy.typing import ArrayLike, NDArray

from sailrouter.weather.wind_grid import WindGrid

MS_TO_KN = 3600.0 / 1852.0


class WindField:
    """Wind of ONE forecast (the deterministic GFS, or one GEFS member) over space and time.

    Bilinear in space, linear in time, on the U/V components (never on speed/direction). Positions outside
    the grid take the nearest edge value; times outside the forecast take the first/last field.
    """

    def __init__(self, grids: Sequence[WindGrid]) -> None:
        if not grids:
            raise ValueError("a wind field needs at least one grid")
        ordered = sorted(grids, key=lambda grid: grid.valid_time)
        first = ordered[0]
        if first.lat_deg.size < 2 or first.lon_deg.size < 2:
            raise ValueError("a wind grid needs at least 2 × 2 points")
        for grid in ordered[1:]:
            if not (np.array_equal(grid.lat_deg, first.lat_deg) and np.array_equal(grid.lon_deg, first.lon_deg)):
                raise ValueError("all grids of a wind field must share the same lat/lon grid")
        self._times_s = np.array([grid.valid_time.timestamp() for grid in ordered])
        self._lat0, self._dlat = float(first.lat_deg[0]), _step(first.lat_deg)
        self._lon0, self._dlon = float(first.lon_deg[0]), _step(first.lon_deg)
        self._u = np.stack([grid.u_ms for grid in ordered])
        self._v = np.stack([grid.v_ms for grid in ordered])

    @property
    def first_time(self) -> datetime:
        return datetime.fromtimestamp(self._times_s[0], UTC)

    @property
    def last_time(self) -> datetime:
        return datetime.fromtimestamp(self._times_s[-1], UTC)

    def wind_at(self, lat_deg: ArrayLike, lon_deg: ArrayLike, time_s: float) -> tuple[NDArray, NDArray]:
        """True wind speed (kn) and direction the wind comes FROM (deg, [0, 360)) at one time (epoch s)."""
        k, weight = self._time_bracket(time_s)
        rows, cols, ty, tx = self._space_bracket(np.asarray(lat_deg, float), np.asarray(lon_deg, float))
        u = self._blend(self._u, k, weight, rows, cols, ty, tx)
        v = self._blend(self._v, k, weight, rows, cols, ty, tx)
        tws_kn = np.hypot(u, v) * MS_TO_KN
        twd_deg = np.degrees(np.arctan2(-u, -v)) % 360.0
        return tws_kn, twd_deg

    def _time_bracket(self, time_s: float) -> tuple[int, float]:
        if self._times_s.size == 1:
            return 0, 0.0
        k = int(np.clip(np.searchsorted(self._times_s, time_s, side="right") - 1, 0, self._times_s.size - 2))
        span = self._times_s[k + 1] - self._times_s[k]
        return k, float(np.clip((time_s - self._times_s[k]) / span, 0.0, 1.0))

    def _space_bracket(self, lat: NDArray, lon: NDArray) -> tuple[NDArray, NDArray, NDArray, NDArray]:
        n_lat, n_lon = self._u.shape[1:]
        fy = np.clip((lat - self._lat0) / self._dlat, 0, n_lat - 1)
        fx = np.clip((lon - self._lon0) / self._dlon, 0, n_lon - 1)
        rows = np.minimum(fy.astype(np.intp), n_lat - 2)
        cols = np.minimum(fx.astype(np.intp), n_lon - 2)
        return rows, cols, fy - rows, fx - cols

    @staticmethod
    def _blend(field: NDArray, k: int, weight: float, rows, cols, ty, tx) -> NDArray:
        def bilinear(layer: NDArray) -> NDArray:
            top = layer[rows, cols] * (1 - tx) + layer[rows, cols + 1] * tx
            bottom = layer[rows + 1, cols] * (1 - tx) + layer[rows + 1, cols + 1] * tx
            return top * (1 - ty) + bottom * ty

        now = bilinear(field[k])
        if weight == 0.0 or field.shape[0] == 1:
            return now
        return now * (1 - weight) + bilinear(field[k + 1]) * weight


def _step(axis: NDArray) -> float:
    return float(axis[1] - axis[0])
