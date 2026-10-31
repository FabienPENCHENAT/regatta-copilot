from __future__ import annotations

from pydantic import BaseModel, Field

from sailrouter.polar.boat_options import OPTIONAL_SAILS, BoatOptions
from sailrouter.polar.winch_timings import ManeuverTiming


class PositionIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class BoatOptionsIn(BaseModel):
    """Owned optional sails, as sent by the settings dialog. Unknown sail names are ignored.

    The site routes on sails and polar speeds only: foils, polished hull and pro winch are never applied
    (the player's choice: the advice gives directions, the player recomputes as the boat goes)."""

    sails: list[str] = []

    def to_options(self) -> BoatOptions:
        owned = frozenset(sail for sail in self.sails if sail in OPTIONAL_SAILS)
        return BoatOptions(sails=owned, foil=False, hull=False, pro_winch=False)


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

    def maneuver_timings(self) -> dict[str, ManeuverTiming]:
        return {name: maneuver.to_timing() for name, maneuver in self.maneuvers.items()}
