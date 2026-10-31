from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.great_circle import GreatCircle
from sailrouter.domain.race import Race
from sailrouter.domain.segment_intersector import SegmentIntersector
from sailrouter.routing.course_leg import CourseLeg

NM_PER_DEG_LAT = 60.0


class MarkProgress:
    """Which mark is next for each point, and whether a step passes it.

    V1 simplification: gates and lines (Fréhel gate, finish) must be crossed in the right direction;
    `point` marks are waypoints reached within `waypoint_radius_nm` (the side they are left to is not
    checked); `island` marks are skipped (land avoidance keeps the boat off them).
    Leg index `len(legs)` means finished.
    """

    def __init__(self, legs: Sequence[CourseLeg]) -> None:
        if not legs:
            raise ValueError("a course needs at least one leg")
        self.legs = tuple(legs)
        lengths = [GreatCircle.distance_nm(a.target.lat_deg, a.target.lon_deg, b.target.lat_deg, b.target.lon_deg)
                   for a, b in zip(self.legs, self.legs[1:])]
        # remaining[k] = distance from the target of leg k to the finish, through the following targets
        self._remaining_nm = np.cumsum([0.0, *lengths[::-1]])[::-1]
        self._target_lat = np.array([leg.target.lat_deg for leg in self.legs])
        self._target_lon = np.array([leg.target.lon_deg for leg in self.legs])

    @classmethod
    def from_race(
        cls, race: Race, start: GeoPoint, first_mark_id: str | None = None, waypoint_radius_nm: float = 2.0
    ) -> MarkProgress:
        """Legs from `start` to the finish. `first_mark_id` skips the marks before it (already passed)."""
        marks = (*race.marks, race.finish)
        if first_mark_id is not None:
            marks = marks[marks.index(race.mark(first_mark_id)):]
        legs: list[CourseLeg] = []
        anchor = start
        for mark in marks:
            if mark.kind == "island":
                continue
            line = (mark.points[0], mark.points[1]) if mark.is_line else None
            radius = 0.0 if line else waypoint_radius_nm
            legs.append(CourseLeg(mark.id, anchor, mark.centre, line, mark.cross, radius))
            anchor = mark.centre
        return cls(legs)

    @property
    def finished_leg(self) -> int:
        return len(self.legs)

    def advance(self, leg: NDArray, lat0: NDArray, lon0: NDArray, lat1: NDArray, lon1: NDArray) -> NDArray:
        """New leg index after sailing each segment (at most one mark passed per step)."""
        new_leg = leg.copy()
        for k in np.unique(leg):
            if k >= self.finished_leg:
                continue
            on_leg = leg == k
            passed = self._passes(self.legs[k], lat0[on_leg], lon0[on_leg], lat1[on_leg], lon1[on_leg])
            new_leg[np.nonzero(on_leg)[0][passed]] = k + 1
        return new_leg

    def distance_to_go_nm(self, leg: NDArray, lat: NDArray, lon: NDArray) -> NDArray:
        """Distance to the next mark, then mark to mark to the finish (0 once finished)."""
        k = np.minimum(leg, self.finished_leg - 1)
        to_go = GreatCircle.distance_nm(lat, lon, self._target_lat[k], self._target_lon[k]) + self._remaining_nm[k]
        return np.where(leg >= self.finished_leg, 0.0, to_go)

    @staticmethod
    def _passes(leg: CourseLeg, lat0, lon0, lat1, lon1) -> NDArray[np.bool_]:
        if leg.line is None:
            return _closest_approach_nm(leg.target, lat0, lon0, lat1, lon1) <= leg.radius_nm
        a, b = leg.line
        crossed = SegmentIntersector.intersects(lon0, lat0, lon1, lat1, a.lon_deg, a.lat_deg, b.lon_deg, b.lat_deg)
        direction = {
            "westward": lon1 < lon0,
            "eastward": lon1 > lon0,
            "northward": lat1 > lat0,
            "southward": lat1 < lat0,
        }.get(leg.cross or "", True)
        return crossed & direction


def _closest_approach_nm(target: GeoPoint, lat0, lon0, lat1, lon1) -> NDArray:
    """Smallest distance between `target` and each segment, on a local flat projection around the target."""
    scale_x = np.cos(np.radians(target.lat_deg)) * NM_PER_DEG_LAT
    x0, y0 = (lon0 - target.lon_deg) * scale_x, (lat0 - target.lat_deg) * NM_PER_DEG_LAT
    x1, y1 = (lon1 - target.lon_deg) * scale_x, (lat1 - target.lat_deg) * NM_PER_DEG_LAT
    dx, dy = x1 - x0, y1 - y0
    length2 = dx * dx + dy * dy
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(length2 > 0, np.clip(-(x0 * dx + y0 * dy) / length2, 0.0, 1.0), 0.0)
    return np.hypot(x0 + t * dx, y0 + t * dy)
