from __future__ import annotations

from dataclasses import dataclass

from sailrouter.domain.geo_point import GeoPoint


@dataclass(frozen=True)
class RaceBoat:
    """One boat class entered in a race: its polar file (relative to the repo root) and its start line."""

    id: str
    polar_path: str | None
    start_line: tuple[GeoPoint, GeoPoint]

    @property
    def start_centre(self) -> GeoPoint:
        a, b = self.start_line
        return GeoPoint((a.lat_deg + b.lat_deg) / 2, (a.lon_deg + b.lon_deg) / 2)
