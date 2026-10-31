from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray


@dataclass(frozen=True)
class RasterGrid:
    """A regular lat/lon raster: cell (row, col) covers `south + row·res … + res`, `west + col·res … + res`."""

    south_deg: float
    west_deg: float
    north_deg: float
    east_deg: float
    resolution_deg: float

    @property
    def n_rows(self) -> int:
        return math.ceil(round((self.north_deg - self.south_deg) / self.resolution_deg, 9))

    @property
    def n_cols(self) -> int:
        return math.ceil(round((self.east_deg - self.west_deg) / self.resolution_deg, 9))

    def cells(self, lat_deg: ArrayLike, lon_deg: ArrayLike) -> tuple[NDArray, NDArray, NDArray]:
        """Row and column of each point, and whether the point lies inside the grid."""
        rows = np.floor((np.asarray(lat_deg, float) - self.south_deg) / self.resolution_deg).astype(np.intp)
        cols = np.floor((np.asarray(lon_deg, float) - self.west_deg) / self.resolution_deg).astype(np.intp)
        inside = (rows >= 0) & (rows < self.n_rows) & (cols >= 0) & (cols < self.n_cols)
        return np.where(inside, rows, 0), np.where(inside, cols, 0), inside

    def coarsened(self, factor: int) -> RasterGrid:
        return RasterGrid(self.south_deg, self.west_deg, self.north_deg, self.east_deg, self.resolution_deg * factor)
