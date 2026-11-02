from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.great_circle import GreatCircle

COMPASS = (("north", 0.0), ("east", 90.0), ("south", 180.0), ("west", 270.0))
OUTER_SUFFIXES = ("", "_wide", "_far")
Position = tuple[float, float]


class OptionLabeler:
    """Names the options (`direct`, `north`, `north_wide`, `south`...) and gives their kind.

    The reference is fixed: the great circle from the boat to the next mark, so a name keeps its meaning from one
    run to the next (the members' consensus track moved with each run and renamed unchanged options). Each
    option's side is its cross-track offset from that line, positive to the right: gap at +48 h + `early_weight`
    × gap at +24 h (the scale of `RouteDistanceMatrix`). The option nearest the line is `direct` when its side is
    within `direct_radius_nm` (150: about 50 nm off the line on average). On each side, options take the compass
    name closest to that side of the heading to the mark (on a westward course: right = `north`, left = `south`),
    the nearest plain, the next ones `_wide`, then `_far`. Kind: `shortest` for the option closest to the leg's great circle, else `positioning`.
    A single option is `consensus` / `consensus`.
    """

    def __init__(self, direct_radius_nm: float = 150.0, early_weight: float = 2.0) -> None:
        self._direct_radius_nm = direct_radius_nm
        self._early_weight = early_weight

    def label(
        self, early: Sequence[Position], late: Sequence[Position], origin: GeoPoint, course: tuple[GeoPoint, GeoPoint],
    ) -> list[tuple[str, str]]:
        """`early` / `late`: one representative (lat, lon) per option at +24 h / +48 h; `course`: leg anchor and
        next mark."""
        if len(late) == 1:
            return [("consensus", "consensus")]
        target = course[1]
        heading = float(GreatCircle.bearing_deg(origin.lat_deg, origin.lon_deg, target.lat_deg, target.lon_deg))
        sides = self._sides(early, late, origin, target)
        ids = self._names(sides, heading)
        shortest = self._closest_to_course(late, course)
        return [(name, "shortest" if k == shortest else "positioning") for k, name in enumerate(ids)]

    def _sides(self, early, late, origin: GeoPoint, target: GeoPoint) -> np.ndarray:
        def cross(points: Sequence[Position]) -> np.ndarray:
            lat, lon = np.array([p[0] for p in points]), np.array([p[1] for p in points])
            return GreatCircle.cross_track_nm(origin.lat_deg, origin.lon_deg, target.lat_deg, target.lon_deg, lat, lon)

        return cross(late) + self._early_weight * cross(early)

    def _names(self, sides: np.ndarray, heading_deg: float) -> list[str]:
        names: dict[int, str] = {}
        order = sorted(range(len(sides)), key=lambda k: (abs(sides[k]), k))
        if abs(sides[order[0]]) <= self._direct_radius_nm:
            names[order.pop(0)] = "direct"
        for right in (True, False):
            side_bearing = heading_deg + (90.0 if right else -90.0)
            compass = min(COMPASS, key=lambda item: _gap(item[1], side_bearing))[0]
            on_side = [k for k in order if (sides[k] >= 0) == right]  # already nearest first
            for rank, k in enumerate(on_side):
                names[k] = compass + OUTER_SUFFIXES[min(rank, len(OUTER_SUFFIXES) - 1)]
        return [names[k] for k in range(len(sides))]

    @staticmethod
    def _closest_to_course(positions: Sequence[Position], course: tuple[GeoPoint, GeoPoint]) -> int:
        anchor, target = course
        lat = np.array([p[0] for p in positions])
        lon = np.array([p[1] for p in positions])
        off = np.abs(GreatCircle.cross_track_nm(anchor.lat_deg, anchor.lon_deg, target.lat_deg, target.lon_deg, lat, lon))
        return int(np.argmin(off))


def _gap(a_deg: float, b_deg: float) -> float:
    return abs((a_deg - b_deg + 180.0) % 360.0 - 180.0)
