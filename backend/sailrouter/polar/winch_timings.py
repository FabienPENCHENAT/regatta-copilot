from __future__ import annotations

from dataclasses import dataclass

MANEUVERS = ("tack", "gybe", "sailChange")


@dataclass(frozen=True)
class ManeuverTiming:
    """During `timer_s` after a maneuver the boat sails at `ratio` × its polar speed, in light / heavy wind."""

    light_timer_s: float
    light_ratio: float
    heavy_timer_s: float
    heavy_ratio: float


@dataclass(frozen=True)
class WinchTimings:
    """VR polar `winch` block: one timing per maneuver (`tack`, `gybe`, `sailChange`) and winch level
    (`std`, `pro`), plus the wind speeds defining "light" (`lws`) and "heavy" (`hws`) wind."""

    timings: dict[tuple[str, str], ManeuverTiming]
    light_wind_kn: float
    heavy_wind_kn: float

    def timing(self, maneuver: str, level: str) -> ManeuverTiming:
        return self.timings[(maneuver, level)]
