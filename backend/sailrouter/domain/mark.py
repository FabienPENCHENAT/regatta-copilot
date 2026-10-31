from __future__ import annotations

from dataclasses import dataclass

from sailrouter.domain.geo_point import GeoPoint

LINE_KINDS = ("gate", "line")
POINT_KINDS = ("point", "island")


@dataclass(frozen=True)
class Mark:
    """One course mark, in race order.

    `kind` is `gate` or `line` (two `points`, crossed in direction `cross`: `westward`, `northward`...) or
    `point` / `island` (one point, left to `leave_to`: `port` or `starboard`).
    """

    id: str
    kind: str
    points: tuple[GeoPoint, ...]
    cross: str | None = None
    leave_to: str | None = None

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
    def centre(self) -> GeoPoint:
        """Middle of a gate or line, or the mark position."""
        if not self.is_line:
            return self.points[0]
        a, b = self.points
        return GeoPoint((a.lat_deg + b.lat_deg) / 2, (a.lon_deg + b.lon_deg) / 2)
