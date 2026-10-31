from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeoPoint:
    """A latitude/longitude pair in decimal degrees. Longitude is normalised to [-180, 180)."""

    lat_deg: float
    lon_deg: float

    def __post_init__(self) -> None:
        if not -90.0 <= self.lat_deg <= 90.0:
            raise ValueError(f"latitude out of range: {self.lat_deg}")
        object.__setattr__(self, "lon_deg", (self.lon_deg + 180.0) % 360.0 - 180.0)

    @classmethod
    def from_lat_lon(cls, pair: list[float] | tuple[float, float]) -> GeoPoint:
        """Builds a point from a `[lat, lon]` pair, the order used in the race files."""
        lat, lon = pair
        return cls(float(lat), float(lon))

    def as_lat_lon(self) -> list[float]:
        return [self.lat_deg, self.lon_deg]
