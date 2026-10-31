from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WeatherArea:
    """Geographic box of the weather download, in degrees (west/east in [-180, 180))."""

    south_deg: float = 0.0
    north_deg: float = 60.0
    west_deg: float = -80.0
    east_deg: float = 10.0
