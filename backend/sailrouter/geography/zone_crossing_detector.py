from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from sailrouter.domain.exclusion_zone import ExclusionZone
from sailrouter.domain.segment_intersector import SegmentIntersector


class ZoneCrossingDetector:
    """Whether segments enter a race exclusion zone.

    Planar geometry in (lon, lat) degrees, exact for the straight lat/lon segment (zones are small).
    - `polygon`: forbidden if the segment ends inside, or crosses the border while starting outside
      (a boat that starts inside may leave).
    - `line`: forbidden if the segment touches the polyline.
    """

    def __init__(self, zones: Sequence[ExclusionZone]) -> None:
        self._zones = [self._prepare(zone) for zone in zones]

    @staticmethod
    def _prepare(zone: ExclusionZone) -> tuple[bool, NDArray, NDArray]:
        points = np.array([[p.lon_deg, p.lat_deg] for p in zone.points])
        is_polygon = zone.shape == "polygon"
        ends = np.roll(points, -1, axis=0) if is_polygon else points[1:]
        starts = points if is_polygon else points[:-1]
        edges = np.hstack([starts, ends])  # x1, y1, x2, y2
        bbox = np.array([points[:, 0].min(), points[:, 1].min(), points[:, 0].max(), points[:, 1].max()])
        return is_polygon, edges, bbox

    def blocked(self, lat0: NDArray, lon0: NDArray, lat1: NDArray, lon1: NDArray) -> NDArray[np.bool_]:
        result = np.zeros(np.shape(lat0), dtype=bool)
        for is_polygon, edges, bbox in self._zones:
            near = (
                (np.maximum(lon0, lon1) >= bbox[0])
                & (np.minimum(lon0, lon1) <= bbox[2])
                & (np.maximum(lat0, lat1) >= bbox[1])
                & (np.minimum(lat0, lat1) <= bbox[3])
            )
            if not near.any():
                continue
            idx = np.nonzero(near)[0]
            x0, y0, x1, y1 = lon0[idx], lat0[idx], lon1[idx], lat1[idx]
            crosses = SegmentIntersector.intersects(
                x0[:, None], y0[:, None], x1[:, None], y1[:, None], *(edges[:, k][None, :] for k in range(4))
            ).any(axis=1)
            if is_polygon:
                crosses = (crosses & ~_inside(x0, y0, edges)) | _inside(x1, y1, edges)
            result[idx] |= crosses
        return result


def _inside(x: NDArray, y: NDArray, edges: NDArray) -> NDArray[np.bool_]:
    """Even-odd ray casting of points against a closed polygon given by its edges."""
    x, y = x[:, None], y[:, None]
    ax, ay, bx, by = (edges[:, k][None, :] for k in range(4))
    straddles = (ay > y) != (by > y)
    with np.errstate(divide="ignore", invalid="ignore"):
        x_cross = ax + (y - ay) * (bx - ax) / (by - ay)
    return (straddles & (x < x_cross)).sum(axis=1) % 2 == 1
