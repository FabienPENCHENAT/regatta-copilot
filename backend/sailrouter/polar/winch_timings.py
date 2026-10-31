from __future__ import annotations

from dataclasses import dataclass, replace

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

    def with_overrides(self, level: str, overrides: dict[str, ManeuverTiming]) -> WinchTimings:
        """A copy where the player's own values replace the game's for some maneuvers at one winch level."""
        timings = dict(self.timings)
        for maneuver, timing in overrides.items():
            if maneuver not in MANEUVERS:
                raise ValueError(f"unknown maneuver {maneuver!r} (known: {', '.join(MANEUVERS)})")
            timings[(maneuver, level)] = timing
        return replace(self, timings=timings)
