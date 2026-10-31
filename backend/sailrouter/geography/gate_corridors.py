from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

from sailrouter.domain.mark import Mark
from sailrouter.geography.raster_grid import RasterGrid


class GateCorridors:
    """Re-opens the coast margin around course gates and lines: the race committee places them in navigable
    water, so within `reach_nm` of a gate only the real coastline counts (a 1 nm gate next to a cape, such as
    Fréhel, would otherwise be nearly closed by the margin)."""

    def __init__(self, reach_nm: float) -> None:
        self._reach_nm = reach_nm

    def open(self, grid: RasterGrid, margin: NDArray[np.uint8], land: NDArray[np.uint8],
             marks: list[Mark]) -> NDArray[np.uint8]:
        opened = margin.copy()
        for mark in marks:
            if mark.is_line:
                self._open_around(grid, opened, land, mark)
        return opened

    def _open_around(self, grid: RasterGrid, margin: NDArray[np.uint8], land: NDArray[np.uint8], mark: Mark) -> None:
        a, b = mark.points
        res = grid.resolution_deg
        mid_cos = math.cos(math.radians((a.lat_deg + b.lat_deg) / 2))
        reach_lat, reach_lon = self._reach_nm / 60.0, self._reach_nm / 60.0 / mid_cos
        row0 = max(0, math.floor((min(a.lat_deg, b.lat_deg) - reach_lat - grid.south_deg) / res))
        row1 = min(grid.n_rows, math.ceil((max(a.lat_deg, b.lat_deg) + reach_lat - grid.south_deg) / res) + 1)
        byte0 = max(0, math.floor((min(a.lon_deg, b.lon_deg) - reach_lon - grid.west_deg) / res) // 8)
        byte1 = min(margin.shape[1], math.ceil((max(a.lon_deg, b.lon_deg) + reach_lon - grid.west_deg) / res) // 8 + 1)
        if row0 >= row1 or byte0 >= byte1:
            return
        lat = grid.south_deg + (np.arange(row0, row1) + 0.5) * res
        lon = grid.west_deg + (np.arange(byte0 * 8, byte1 * 8) + 0.5) * res
        near = self._distance_nm(lat[:, None], lon[None, :], a, b, mid_cos) <= self._reach_nm
        window = np.unpackbits(margin[row0:row1, byte0:byte1], axis=1).astype(bool)
        real = np.unpackbits(land[row0:row1, byte0:byte1], axis=1).astype(bool)
        margin[row0:row1, byte0:byte1] = np.packbits(np.where(near, real, window), axis=1)

    @staticmethod
    def _distance_nm(lat, lon, a, b, cos_lat) -> NDArray[np.float64]:
        """Distance to the segment a–b on a local flat projection (nm), fine over a few miles."""
        ax, ay = a.lon_deg * cos_lat * 60, a.lat_deg * 60
        bx, by = b.lon_deg * cos_lat * 60, b.lat_deg * 60
        px, py = lon * cos_lat * 60, lat * 60
        dx, dy = bx - ax, by - ay
        t = np.clip(((px - ax) * dx + (py - ay) * dy) / max(dx * dx + dy * dy, 1e-12), 0.0, 1.0)
        return np.hypot(px - (ax + t * dx), py - (ay + t * dy))
