from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from shapely.geometry import Polygon

from sailrouter.geography.raster_grid import RasterGrid

ROWS_PER_CHUNK = 512


class PolygonRasterizer:
    """Burns polygons into a bit-packed boolean raster: a cell is set when its CENTRE is inside a polygon.

    Scanline fill with the non-zero winding rule (so overlapping polygons are a union and holes stay empty,
    given oriented polygons). Pure numpy: every edge is cut against the row centres it spans, then a running
    sum of the crossing directions along each row gives the winding number of every cell.
    Output: `np.packbits(mask, axis=1)`, shape `(n_rows, ceil(n_cols / 8))`.
    """

    def __init__(self, grid: RasterGrid) -> None:
        self._grid = grid

    def rasterize(self, polygons: list[Polygon]) -> NDArray[np.uint8]:
        rows, cols, directions = self._crossings(self._edges(polygons))
        order = np.argsort(rows, kind="stable")
        rows, cols, directions = rows[order], cols[order], directions[order]
        n_rows, n_cols = self._grid.n_rows, self._grid.n_cols
        packed = np.zeros((n_rows, (n_cols + 7) // 8), dtype=np.uint8)
        for start in range(0, n_rows, ROWS_PER_CHUNK):
            stop = min(start + ROWS_PER_CHUNK, n_rows)
            low, high = np.searchsorted(rows, [start, stop])
            diff = np.zeros((stop - start, n_cols + 1), dtype=np.int32)
            np.add.at(diff, (rows[low:high] - start, cols[low:high]), directions[low:high])
            winding = np.cumsum(diff[:, :n_cols], axis=1)
            packed[start:stop] = np.packbits(winding != 0, axis=1)
        return packed

    @staticmethod
    def _edges(polygons: list[Polygon]) -> NDArray:
        """All ring edges as an `(n, 4)` array of `lon1, lat1, lon2, lat2`."""
        segments = []
        for polygon in polygons:
            for ring in (polygon.exterior, *polygon.interiors):
                coords = np.asarray(ring.coords)[:, :2]
                segments.append(np.hstack([coords[:-1], coords[1:]]))
        return np.vstack(segments) if segments else np.zeros((0, 4))

    def _crossings(self, edges: NDArray) -> tuple[NDArray, NDArray, NDArray]:
        """Row, first column right of the crossing, and direction (+1 up, −1 down) of every edge × row centre."""
        grid = self._grid
        x1, y1, x2, y2 = edges.T
        moving = y1 != y2
        x1, y1, x2, y2 = x1[moving], y1[moving], x2[moving], y2[moving]
        to_row = lambda y: np.ceil((y - grid.south_deg) / grid.resolution_deg - 0.5)  # noqa: E731
        first = np.clip(to_row(np.minimum(y1, y2)), 0, grid.n_rows).astype(np.intp)
        last = np.clip(to_row(np.maximum(y1, y2)), 0, grid.n_rows).astype(np.intp)
        counts = last - first
        edge = np.repeat(np.arange(counts.size), counts)
        offsets = np.arange(edge.size) - np.repeat(np.cumsum(counts) - counts, counts)
        rows = first[edge] + offsets
        y_centre = grid.south_deg + (rows + 0.5) * grid.resolution_deg
        x = x1[edge] + (y_centre - y1[edge]) * (x2[edge] - x1[edge]) / (y2[edge] - y1[edge])
        cols = np.ceil((x - grid.west_deg) / grid.resolution_deg - 0.5)
        cols = np.clip(cols, 0, grid.n_cols).astype(np.intp)
        directions = np.where(y2[edge] > y1[edge], 1, -1).astype(np.int32)
        return rows, cols, directions
