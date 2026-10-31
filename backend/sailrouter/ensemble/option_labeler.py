from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.great_circle import GreatCircle

COMPASS = (("north", 0.0), ("east", 90.0), ("south", 180.0), ("west", 270.0))
Position = tuple[float, float]


class OptionLabeler:
    """Names the options (`direct`, `north`, `south`, `west`, `east`) and gives their kind.

    Each option's side is its offset from the consensus track (origin → median position of all members at
    +48 h), positive to the right: cross-track gap at +48 h + `early_weight` × gap at +24 h (the scale of
    `RouteDistanceMatrix`). The most central option is `direct` when its side is within `direct_radius_nm`.
    The others, outermost first, take the compass name closest to their side of the consensus heading (on a
    westward course: right = `north`, left = `south`); when it is taken, the next closest name, the heading's
    own direction first. Kind: `shortest` for the option closest to the great circle to the next mark, else
    `positioning`. A single option is `consensus` / `consensus`.
    """

    def __init__(self, direct_radius_nm: float = 60.0, early_weight: float = 2.0) -> None:
        self._direct_radius_nm = direct_radius_nm
        self._early_weight = early_weight

    def label(
        self, early: Sequence[Position], late: Sequence[Position], consensus_early: Position,
        consensus_late: Position, origin: GeoPoint, course: tuple[GeoPoint, GeoPoint],
    ) -> list[tuple[str, str]]:
        """`early` / `late`: one representative (lat, lon) per option at +24 h / +48 h."""
        if len(late) == 1:
            return [("consensus", "consensus")]
        heading = float(GreatCircle.bearing_deg(origin.lat_deg, origin.lon_deg, *consensus_late))
        sides = self._sides(early, late, consensus_early, consensus_late, origin)
        ids = self._names(sides, heading)
        shortest = self._closest_to_course(late, course)
        return [(name, "shortest" if k == shortest else "positioning") for k, name in enumerate(ids)]

    def _sides(self, early, late, consensus_early, consensus_late, origin: GeoPoint) -> np.ndarray:
        def cross(points: Sequence[Position]) -> np.ndarray:
            lat, lon = np.array([p[0] for p in points]), np.array([p[1] for p in points])
            return GreatCircle.cross_track_nm(origin.lat_deg, origin.lon_deg, *consensus_late, lat, lon)

        late_gap = cross(late) - cross([consensus_late])[0]
        early_gap = cross(early) - cross([consensus_early])[0]
        return late_gap + self._early_weight * early_gap

    def _names(self, sides: np.ndarray, heading_deg: float) -> list[str]:
        names: dict[int, str] = {}
        order = sorted(range(len(sides)), key=lambda k: (abs(sides[k]), k))
        if abs(sides[order[0]]) <= self._direct_radius_nm:
            names[order.pop(0)] = "direct"
        for k in reversed(order):
            side_bearing = heading_deg + (90.0 if sides[k] >= 0 else -90.0)
            # compass names by closeness to the side (in 45° steps, so a 0.2° difference is no reason), then to the heading
            ranked = sorted(COMPASS, key=lambda item: (round(_gap(item[1], side_bearing) / 45.0),
                                                       _gap(item[1], heading_deg)))
            names[k] = next(name for name, _ in (*ranked, ("direct", 0.0)) if name not in names.values())
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
