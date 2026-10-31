from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.great_circle import GreatCircle

COMPASS = (("north", 0.0), ("east", 90.0), ("south", 180.0), ("west", 270.0))
NM_PER_DEG = 60.0


class OptionLabeler:
    """Names the options (`direct`, `north`, `south`, `west`, `east`) and gives their kind.

    - id: where the option's +48 h position lies from the consensus position (median of all members at
      +48 h): within `direct_radius_nm` → `direct`, else the compass direction of the offset. Options are
      named by decreasing probability; when a name is taken, the next closest direction is used.
    - kind: `shortest` for the option closest to the great-circle course to the next mark, `positioning`
      for the others. A single option is `consensus` / `consensus`.
    """

    def __init__(self, direct_radius_nm: float = 30.0) -> None:
        self._direct_radius_nm = direct_radius_nm

    def label(
        self, positions_48h: Sequence[tuple[float, float]], consensus: tuple[float, float],
        course: tuple[GeoPoint, GeoPoint],
    ) -> list[tuple[str, str]]:
        """`positions_48h`: one representative (lat, lon) per option, most probable first."""
        if len(positions_48h) == 1:
            return [("consensus", "consensus")]
        taken: set[str] = set()
        ids = []
        for position in positions_48h:
            name = next(label for label in self._preferences(position, consensus) if label not in taken)
            taken.add(name)
            ids.append(name)
        shortest = self._closest_to_course(positions_48h, course)
        return [(name, "shortest" if k == shortest else "positioning") for k, name in enumerate(ids)]

    def _preferences(self, position: tuple[float, float], consensus: tuple[float, float]) -> list[str]:
        east_nm = (position[1] - consensus[1]) * NM_PER_DEG * math.cos(math.radians(consensus[0]))
        north_nm = (position[0] - consensus[0]) * NM_PER_DEG
        bearing = math.degrees(math.atan2(east_nm, north_nm)) % 360.0
        by_angle = [name for name, _ in sorted(COMPASS, key=lambda item: (_angle_gap(bearing, item[1]), item[1]))]
        if math.hypot(east_nm, north_nm) <= self._direct_radius_nm:
            return ["direct", *by_angle]
        return [*by_angle, "direct"]

    @staticmethod
    def _closest_to_course(positions: Sequence[tuple[float, float]], course: tuple[GeoPoint, GeoPoint]) -> int:
        anchor, target = course
        lat = np.array([p[0] for p in positions])
        lon = np.array([p[1] for p in positions])
        off = np.abs(GreatCircle.cross_track_nm(anchor.lat_deg, anchor.lon_deg, target.lat_deg, target.lon_deg, lat, lon))
        return int(np.argmin(off))


def _angle_gap(a_deg: float, b_deg: float) -> float:
    return abs((a_deg - b_deg + 180.0) % 360.0 - 180.0)
