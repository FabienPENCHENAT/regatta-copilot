from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from sailrouter.geography.raster_grid import RasterGrid

COARSE_FACTOR = 16
MAX_CLEARANCE_CELLS = 32  # distances to land are measured up to 32 coarse cells (≈ 2.6°); farther counts as 32


class LandMask:
    """Fast "is this point on land?" lookup on a bit-packed raster. Points outside the raster count as land
    (the boat must stay inside the weather area).

    Also keeps a coarse raster (`COARSE_FACTOR` × coarser, dilated by one cell) answering "may there be land
    within one coarse cell of this point?", and a clearance map: how far (in degrees, Chebyshev metric on the
    lat/lon raster) the nearest land or raster edge is at least. Both let the checker skip work far from coasts.
    """

    def __init__(self, grid: RasterGrid, packed: NDArray[np.uint8]) -> None:
        expected = (grid.n_rows, (grid.n_cols + 7) // 8)
        if packed.shape != expected:
            raise ValueError(f"packed raster shape {packed.shape}, expected {expected}")
        self.grid = grid
        self._packed = packed
        self.coarse_grid = grid.coarsened(COARSE_FACTOR)
        self._coarse = self._build_coarse()
        self._clearance_cells = self._build_clearance()

    def is_land(self, lat_deg: ArrayLike, lon_deg: ArrayLike) -> NDArray[np.bool_]:
        rows, cols, inside = self.grid.cells(lat_deg, lon_deg)
        bits = (self._packed[rows, cols >> 3] >> (7 - (cols & 7))) & 1
        return (bits == 1) | ~inside

    def clearance_deg(self, lat_deg: ArrayLike, lon_deg: ArrayLike) -> NDArray[np.float64]:
        """Lower bound of the distance to land (or the raster edge), in degrees along lat or lon: any point within
        this distance of (lat, lon), both coordinates, is at sea."""
        rows, cols, inside = self.coarse_grid.cells(lat_deg, lon_deg)
        cells = np.where(inside, self._clearance_cells[rows, cols], 0)
        return np.maximum(cells - 1, 0) * self.coarse_grid.resolution_deg

    def may_be_near_land(self, lat_deg: ArrayLike, lon_deg: ArrayLike) -> NDArray[np.bool_]:
        rows, cols, inside = self.coarse_grid.cells(lat_deg, lon_deg)
        return self._coarse[rows, cols] | ~inside

    def _build_coarse(self) -> NDArray[np.bool_]:
        n_rows, n_cols = self.coarse_grid.n_rows, self.coarse_grid.n_cols
        coarse = np.zeros((n_rows, n_cols), dtype=bool)
        packed_cols = COARSE_FACTOR // 8
        for row in range(n_rows):
            block = self._packed[row * COARSE_FACTOR : (row + 1) * COARSE_FACTOR].any(axis=0)
            padded = np.zeros(n_cols * packed_cols, dtype=bool)
            padded[: min(block.size, padded.size)] = block[: padded.size]
            coarse[row] = padded.reshape(n_cols, packed_cols).any(axis=1)
        self._coarse_land = coarse
        return self._dilate(coarse)

    def _build_clearance(self) -> NDArray[np.int16]:
        """Distance in coarse cells to the nearest coarse cell holding land, grown one ring at a time from the
        (undilated) land cells; the raster edge counts as land, including coarse cells that stick out of the
        fine raster (when its size is not a multiple of COARSE_FACTOR)."""
        land = self._coarse_land.copy()
        if self.grid.n_rows % COARSE_FACTOR:
            land[-1, :] = True
        if self.grid.n_cols % COARSE_FACTOR:
            land[:, -1] = True
        land = np.pad(land, 1, constant_values=True)
        distance = np.full(land.shape, MAX_CLEARANCE_CELLS, dtype=np.int16)
        reached = land.copy()
        distance[reached] = 0
        for ring in range(1, MAX_CLEARANCE_CELLS):
            grown = self._dilate(reached)
            distance[grown & ~reached] = ring
            reached = grown
        return distance[1:-1, 1:-1]

    @staticmethod
    def _dilate(mask: NDArray[np.bool_]) -> NDArray[np.bool_]:
        padded = np.pad(mask, 1)
        out = np.zeros_like(mask)
        for dr in (0, 1, 2):
            for dc in (0, 1, 2):
                out |= padded[dr : dr + mask.shape[0], dc : dc + mask.shape[1]]
        return out
