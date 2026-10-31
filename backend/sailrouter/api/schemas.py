from __future__ import annotations

from pydantic import BaseModel, Field

from sailrouter.polar.boat_options import OPTIONAL_SAILS, BoatOptions
from sailrouter.polar.winch_timings import ManeuverTiming


class PositionIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class BoatOptionsIn(BaseModel):
    """VR options owned by the player, as sent by the settings dialog: optional sails (unknown names are
    ignored), foils, polished hull, pro winch. Everything off by default (the bare boat: Jib and Spi)."""

    sails: list[str] = []
    foil: bool = False
    hull: bool = False
    pro_winch: bool = False

    def to_options(self) -> BoatOptions:
        owned = frozenset(sail for sail in self.sails if sail in OPTIONAL_SAILS)
        return BoatOptions(sails=owned, foil=self.foil, hull=self.hull, pro_winch=self.pro_winch)


class ManeuverIn(BaseModel):
    """The player's own maneuver time (defaults come from the polar): slowdown duration in light and strong
    wind, and the speed kept meanwhile."""

    light_min: float = Field(ge=0, le=60)
    strong_min: float = Field(ge=0, le=60)
    speed_percent: float = Field(ge=0, le=100)

    def to_timing(self) -> ManeuverTiming:
        ratio = self.speed_percent / 100
        return ManeuverTiming(self.light_min * 60, ratio, self.strong_min * 60, ratio)


class RouteRequest(BaseModel):
    race_id: str
    boat_id: str | None = None
    position: PositionIn
    options: BoatOptionsIn = BoatOptionsIn()
    maneuvers: dict[str, ManeuverIn] = {}  # keys: tack, gybe, sailChange; missing = the game's values
    next_mark: str | None = None  # id of the next mark to round; None = found from the position

    def maneuver_timings(self) -> dict[str, ManeuverTiming]:
        return {name: maneuver.to_timing() for name, maneuver in self.maneuvers.items()}
