from __future__ import annotations

import math

from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.mark import Mark
from sailrouter.domain.race import Race

PASSED_MARGIN_NM = 2.0  # beyond a gate or line by more than this: it was crossed
AXIS_BY_CROSSING = {"westward": ("lon", -1), "eastward": ("lon", 1), "northward": ("lat", 1), "southward": ("lat", -1)}


class NextMarkFinder:
    """The first course mark still ahead of a position, so a route computed mid-race does not sail back to
    marks already rounded.

    A gate or line counts as passed when the position lies beyond it, in its crossing direction, by more than
    `PASSED_MARGIN_NM`. A point or island mark cannot be judged from a position alone and always counts as ahead
    (the player can still name the next mark explicitly).
    """

    def first_ahead(self, race: Race, position: GeoPoint) -> str:
        for mark in race.marks:
            if not self._passed(mark, position):
                return mark.id
        return race.finish.id

    @staticmethod
    def _passed(mark: Mark, position: GeoPoint) -> bool:
        if not mark.is_line or mark.cross not in AXIS_BY_CROSSING:
            return False
        axis, sign = AXIS_BY_CROSSING[mark.cross]
        if axis == "lat":
            line = max(p.lat_deg for p in mark.points) if sign > 0 else min(p.lat_deg for p in mark.points)
            beyond_nm = (position.lat_deg - line) * sign * 60.0
        else:
            line = min(p.lon_deg for p in mark.points) if sign < 0 else max(p.lon_deg for p in mark.points)
            beyond_nm = (position.lon_deg - line) * sign * 60.0 * math.cos(math.radians(position.lat_deg))
        return beyond_nm > PASSED_MARGIN_NM
