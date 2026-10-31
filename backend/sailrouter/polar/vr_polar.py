from __future__ import annotations

from dataclasses import dataclass

from sailrouter.polar.boat_polar import BoatPolar
from sailrouter.polar.foil_bonus import FoilBonus
from sailrouter.polar.winch_timings import WinchTimings


@dataclass(frozen=True)
class VrPolar:
    """Everything a VR `Meta_GetPolar` file says about a boat: speed tables, foil and hull bonus, winches."""

    label: str
    polar: BoatPolar
    foil: FoilBonus
    hull_ratio: float
    global_speed_ratio: float
    winch: WinchTimings
