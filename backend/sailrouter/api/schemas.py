from __future__ import annotations

from pydantic import BaseModel, Field

from sailrouter.polar.boat_options import OPTIONAL_SAILS, BoatOptions


class PositionIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class BoatOptionsIn(BaseModel):
    """Owned VR options, as sent by the settings dialog. Unknown sail names are ignored."""

    sails: list[str] = []
    foil: bool = True
    hull: bool = False
    pro_winch: bool = False

    def to_options(self) -> BoatOptions:
        owned = frozenset(sail for sail in self.sails if sail in OPTIONAL_SAILS)
        return BoatOptions(sails=owned, foil=self.foil, hull=self.hull, pro_winch=self.pro_winch)


class RouteRequest(BaseModel):
    race_id: str
    boat_id: str | None = None
    position: PositionIn
    options: BoatOptionsIn = BoatOptionsIn()
