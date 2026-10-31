from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from sailrouter.geography.raster_grid import RasterGrid

COARSE_FACTOR = 16


class LandMask:
    """Fast "is this point on land?" lookup on a bit-packed raster. Points outside the raster count as land
    (the boat must stay inside the weather area).

    Also keeps a coarse raster (`COARSE_FACTOR` × coarser, dilated by one cell) answering "may there be land
    within one coarse cell of this point?", used to skip the fine check far from the coast.
    """

    def __init__(self, grid: RasterGrid, packed: NDArray[np.uint8]) -> None:
        expected = (grid.n_rows, (grid.n_cols + 7) // 8)
        if packed.shape != expected:
            raise ValueError(f"packed raster shape {packed.shape}, expected {expected}")
        self.grid = grid
        self._packed = packed
        self.coarse_grid = grid.coarsened(COARSE_FACTOR)
        self._coarse = self._build_coarse()

    def is_land(self, lat_deg: ArrayLike, lon_deg: ArrayLike) -> NDArray[np.bool_]:
        rows, cols, inside = self.grid.cells(lat_deg, lon_deg)
        bits = (self._packed[rows, cols >> 3] >> (7 - (cols & 7))) & 1
        return (bits == 1) | ~inside

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
        return self._dilate(coarse)

    @staticmethod
    def _dilate(mask: NDArray[np.bool_]) -> NDArray[np.bool_]:
        padded = np.pad(mask, 1)
        out = np.zeros_like(mask)
        for dr in (0, 1, 2):
            for dc in (0, 1, 2):
                out |= padded[dr : dr + mask.shape[0], dc : dc + mask.shape[1]]
        return out
