from __future__ import annotations

from dataclasses import dataclass

# VR sail packs: Jib and Spi are always on board; each option pack adds sails.
SAIL_PACKS = {
    "light": ("LightJib", "LightGnk"),
    "heavy": ("Staysail", "HeavyGnk"),
    "reach": ("Code0",),
}
BASE_SAILS = ("Jib", "Spi")


@dataclass(frozen=True)
class BoatOptions:
    """VR options owned by the player. All on by default (the usual "full pack" setting)."""

    light: bool = True
    heavy: bool = True
    reach: bool = True
    foil: bool = True
    hull: bool = True
    pro_winch: bool = True

    def allows_sail(self, sail_name: str) -> bool:
        if sail_name in BASE_SAILS:
            return True
        for pack, sails in SAIL_PACKS.items():
            if sail_name in sails:
                return bool(getattr(self, pack))
        return False
