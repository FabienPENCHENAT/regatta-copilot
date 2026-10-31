from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sailrouter.polar.boat_polar import BoatPolar
from sailrouter.polar.foil_bonus import FoilBonus
from sailrouter.polar.vr_polar import VrPolar
from sailrouter.polar.winch_timings import MANEUVERS, ManeuverTiming, WinchTimings

# VR numbers sails the same way for every boat, but spells their names differently per polar
# ("Jib", "jib", "JIB", "LIGHT_JIB"...). Canonical names come from the sail number.
SAIL_NAMES_BY_ID = {1: "Jib", 2: "Spi", 3: "Staysail", 4: "LightJib", 5: "Code0", 6: "HeavyGnk", 7: "LightGnk"}


class VrPolarParser:
    """Raw VR `Meta_GetPolar` JSON (`tws[]`, `twa[]`, `sail[].speed[twa][tws]`, `foil`, `hull`, `winch`)
    → `VrPolar`."""

    def load(self, path: Path) -> VrPolar:
        return self.parse(json.loads(path.read_text(encoding="utf-8")))

    def parse(self, data: dict[str, Any]) -> VrPolar:
        sails = sorted(data["sail"], key=self._sail_id)
        polar = BoatPolar(
            tws_kn=data["tws"],
            twa_deg=data["twa"],
            sail_names=tuple(SAIL_NAMES_BY_ID.get(self._sail_id(sail), sail["name"]) for sail in sails),
            speeds_kn=[sail["speed"] for sail in sails],
        )
        return VrPolar(
            label=data.get("label", "unknown"),
            polar=polar,
            foil=self._parse_foil(data["foil"]),
            hull_ratio=float(data.get("hull", {}).get("speedRatio", 1.0)),
            global_speed_ratio=float(data.get("globalSpeedRatio", 1.0)),
            winch=self._parse_winch(data["winch"]),
        )

    @staticmethod
    def _sail_id(sail: dict[str, Any]) -> int:
        return int(sail.get("id", sail.get("_id")))

    @staticmethod
    def _parse_foil(foil: dict[str, Any]) -> FoilBonus:
        return FoilBonus(
            speed_ratio=float(foil["speedRatio"]),
            twa_min=float(foil["twaMin"]),
            twa_max=float(foil["twaMax"]),
            twa_merge=float(foil["twaMerge"]),
            tws_min=float(foil["twsMin"]),
            tws_max=float(foil["twsMax"]),
            tws_merge=float(foil["twsMerge"]),
        )

    @staticmethod
    def _parse_winch(winch: dict[str, Any]) -> WinchTimings:
        timings = {}
        for maneuver in MANEUVERS:
            for level in ("std", "pro"):
                block = winch[maneuver][level]
                timings[(maneuver, level)] = ManeuverTiming(
                    light_timer_s=float(block["lw"]["timer"]),
                    light_ratio=float(block["lw"]["ratio"]),
                    heavy_timer_s=float(block["hw"]["timer"]),
                    heavy_ratio=float(block["hw"]["ratio"]),
                )
        return WinchTimings(timings, light_wind_kn=float(winch["lws"]), heavy_wind_kn=float(winch["hws"]))
