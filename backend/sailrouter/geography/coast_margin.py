from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

from sailrouter.geography.raster_grid import RasterGrid

ROWS_PER_BAND = 512


class CoastMargin:
    """Widens the land of a bit-packed raster by a safety margin, in nautical miles, so routes keep clear of
    a coastline that is only approximate (the game's own coast differs from Natural Earth).

    Each land cell grows into an ellipse `margin_nm` wide in both directions: rows of the ellipse are
    horizontal dilations (a window sum on a cumulative sum), with the longitude width taken at the band's
    highest latitude so the margin is never thinner than asked."""

    def __init__(self, margin_nm: float) -> None:
        if margin_nm <= 0:
            raise ValueError("margin must be positive")
        self._margin_nm = margin_nm

    def widen(self, grid: RasterGrid, packed: NDArray[np.uint8]) -> NDArray[np.uint8]:
        n_rows, n_cols, res = grid.n_rows, grid.n_cols, grid.resolution_deg
        reach_rows = math.ceil(self._margin_nm / 60.0 / res)
        widened = np.empty_like(packed)
        for start in range(0, n_rows, ROWS_PER_BAND):
            stop = min(start + ROWS_PER_BAND, n_rows)
            low, high = max(0, start - reach_rows), min(n_rows, stop + reach_rows)
            band = np.unpackbits(packed[low:high], axis=1, count=n_cols).astype(bool)
            widest_lat = max(abs(grid.south_deg + start * res), abs(grid.south_deg + stop * res))
            reach_cols = self._margin_nm / 60.0 / math.cos(math.radians(min(widest_lat, 89.0))) / res
            result = np.zeros((stop - start, n_cols), dtype=bool)
            by_width: dict[int, NDArray[np.bool_]] = {}
            for dy in range(-reach_rows, reach_rows + 1):
                share = 1.0 - (dy * res * 60.0 / self._margin_nm) ** 2
                if share < 0:
                    continue
                dx = math.ceil(reach_cols * math.sqrt(share))
                if dx not in by_width:
                    by_width[dx] = _widen_rows(band, dx)
                first, last = max(start, -dy), min(stop, n_rows - dy)  # rows r whose neighbour r + dy exists
                if first < last:
                    result[first - start : last - start] |= by_width[dx][first + dy - low : last + dy - low]
            widened[start:stop] = np.packbits(result, axis=1)
        return widened


def _widen_rows(band: NDArray[np.bool_], dx: int) -> NDArray[np.bool_]:
    """Each cell set when any cell within `dx` columns on its row is set."""
    n_cols = band.shape[1]
    total = np.zeros((band.shape[0], n_cols + 1), dtype=np.int32)
    np.cumsum(band, axis=1, out=total[:, 1:])
    columns = np.arange(n_cols)
    left, right = np.clip(columns - dx, 0, n_cols), np.clip(columns + dx + 1, 0, n_cols)
    return (total[:, right] - total[:, left]) > 0
