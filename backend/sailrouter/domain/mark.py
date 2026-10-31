from __future__ import annotations

from dataclasses import dataclass

from sailrouter.domain.geo_point import GeoPoint

LINE_KINDS = ("gate", "line")
POINT_KINDS = ("point",)


@dataclass(frozen=True)
class Mark:
    """One course mark, in race order.

    `kind` is `gate` or `line` (two `points`, crossed in direction `cross`: `westward`, `northward`...) or
    `point` (one point, a waypoint). A mark rounded to one side (`leave_to`: `port` or `starboard`) is encoded
    as a directed gate from the physical mark to land or open water, so crossing it in its direction proves the
    side; `position` is then the physical mark (shown on the map, aimed at by the router).
    """

    id: str
    kind: str
    points: tuple[GeoPoint, ...]
    cross: str | None = None
    leave_to: str | None = None
    position: GeoPoint | None = None

    def __post_init__(self) -> None:
        expected = 2 if self.kind in LINE_KINDS else 1 if self.kind in POINT_KINDS else None
        if expected is None:
            raise ValueError(f"mark {self.id}: unknown kind {self.kind!r}")
        if len(self.points) != expected:
            raise ValueError(f"mark {self.id}: {self.kind} needs {expected} point(s)")

    @property
    def is_line(self) -> bool:
        return self.kind in LINE_KINDS

    @property
    def is_rounding(self) -> bool:
        """A mark left to one side: whether it was rounded cannot be told from a position alone."""
        return self.leave_to is not None

    @property
    def centre(self) -> GeoPoint:
        """Middle of a gate or line, or the mark position."""
        if not self.is_line:
            return self.points[0]
        a, b = self.points
        return GeoPoint((a.lat_deg + b.lat_deg) / 2, (a.lon_deg + b.lon_deg) / 2)

    @property
    def target(self) -> GeoPoint:
        """Where the router aims: the physical mark when there is one, else the centre."""
        return self.position or self.centre
