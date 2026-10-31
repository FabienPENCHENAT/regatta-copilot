from __future__ import annotations

from dataclasses import dataclass

from sailrouter.domain.geo_point import GeoPoint


@dataclass(frozen=True)
class CourseLeg:
    """One leg of the routed course: from `anchor` (start or previous mark) to the mark `mark_id`.

    The mark is passed either by crossing `line` (two points) in direction `cross` (`westward`, `northward`,
    ... or None for any), or, without a line, by coming within `radius_nm` of `target`.
    """

    mark_id: str
    anchor: GeoPoint
    target: GeoPoint
    line: tuple[GeoPoint, GeoPoint] | None = None
    cross: str | None = None
    radius_nm: float = 0.0
