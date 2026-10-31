from __future__ import annotations

from dataclasses import dataclass

BASE_SAILS = ("Jib", "Spi")  # always on board in VR
OPTIONAL_SAILS = ("LightJib", "LightGnk", "Staysail", "HeavyGnk", "Code0")
EQUIPMENT = ("foil", "hull", "pro_winch")
# Shorthands for the VR sail packs, kept for the command line.
SAIL_PACKS = {"light": ("LightJib", "LightGnk"), "heavy": ("Staysail", "HeavyGnk"), "reach": ("Code0",)}


@dataclass(frozen=True)
class BoatOptions:
    """VR options owned by the player: optional sails, one by one, and equipment.
    Default: everything (the usual "full pack" setting)."""

    sails: frozenset[str] = frozenset(OPTIONAL_SAILS)
    foil: bool = True
    hull: bool = True
    pro_winch: bool = True

    @classmethod
    def from_owned(cls, owned: str) -> BoatOptions:
        """From a comma-separated list, e.g. "foil", "Code0,LightJib,foil,hull" or "light,foil".
        "all" means everything, "none" the bare boat (Jib and Spi only)."""
        if owned.strip() == "all":
            return cls()
        names = {name.strip() for name in owned.split(",") if name.strip() and name.strip() != "none"}
        sails = set()
        for name in names - set(EQUIPMENT):
            if name in SAIL_PACKS:
                sails.update(SAIL_PACKS[name])
            elif name in OPTIONAL_SAILS:
                sails.add(name)
            else:
                known = ", ".join((*OPTIONAL_SAILS, *SAIL_PACKS, *EQUIPMENT))
                raise ValueError(f"unknown boat option: {name} (known: {known})")
        return cls(sails=frozenset(sails), **{item: item in names for item in EQUIPMENT})

    def allows_sail(self, sail_name: str) -> bool:
        return sail_name in BASE_SAILS or sail_name in self.sails
