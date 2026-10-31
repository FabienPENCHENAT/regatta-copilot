from __future__ import annotations

from dataclasses import dataclass

from sailrouter.domain.geo_point import GeoPoint

SHAPES = ("polygon", "line")


@dataclass(frozen=True)
class ExclusionZone:
    """A forbidden area: a closed `polygon`, or a `line` (polyline) that must not be crossed."""

    id: str
    shape: str
    points: tuple[GeoPoint, ...]
    kind: str = "other"

    def __post_init__(self) -> None:
        if self.shape not in SHAPES:
            raise ValueError(f"zone {self.id}: unknown shape {self.shape!r}")
        minimum = 3 if self.shape == "polygon" else 2
        if len(self.points) < minimum:
            raise ValueError(f"zone {self.id}: a {self.shape} needs at least {minimum} points")
