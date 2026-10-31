from __future__ import annotations

import math
from collections.abc import Sequence

from shapely.geometry import LineString, Polygon

from sailrouter.domain.exclusion_zone import ExclusionZone
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.mark import Mark

ARC_SEGMENTS = 4  # per quarter circle at the corners: enough for a safety margin, few edges to test


class ZoneMargin:
    """Widens the race's exclusion zones by a safety margin (nm), like the coast margin: routes keep clear of
    zone borders the game may draw slightly differently. A polygon grows into a larger polygon, a forbidden
    line into a corridor around it. Zones whose widened shape would touch a course gate or line keep their
    own shape (the committee keeps its gates and finish line usable)."""

    def __init__(self, margin_nm: float) -> None:
        self._margin_nm = margin_nm

    def widen(self, zones: Sequence[ExclusionZone], marks: Sequence[Mark]) -> list[ExclusionZone]:
        return [self._widened(zone, marks) for zone in zones]

    def _widened(self, zone: ExclusionZone, marks: Sequence[Mark]) -> ExclusionZone:
        points = [(p.lon_deg, p.lat_deg) for p in zone.points]
        cos_lat = math.cos(math.radians(sum(lat for _, lat in points) / len(points)))
        to_nm = lambda lon, lat: (lon * cos_lat * 60.0, lat * 60.0)  # noqa: E731 - local flat projection
        projected = [to_nm(lon, lat) for lon, lat in points]
        shape = Polygon(projected) if zone.shape == "polygon" else LineString(projected)
        grown = shape.buffer(self._margin_nm, quad_segs=ARC_SEGMENTS)
        for mark in marks:
            if mark.is_line and grown.intersects(LineString([to_nm(p.lon_deg, p.lat_deg) for p in mark.points])):
                return zone
        ring = list(grown.exterior.coords)[:-1]
        widened = tuple(GeoPoint(y / 60.0, x / cos_lat / 60.0) for x, y in ring)
        return ExclusionZone(zone.id, "polygon", widened, zone.kind)
