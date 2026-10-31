from __future__ import annotations

from dataclasses import dataclass

# VR sail packs: Jib and Spi are always on board; each option pack adds sails.
SAIL_PACKS = {
    "light": ("LightJib", "LightGnk"),
    "heavy": ("Staysail", "HeavyGnk"),
    "reach": ("Code0",),
}
BASE_SAILS = ("Jib", "Spi")
OPTION_NAMES = ("light", "heavy", "reach", "foil", "hull", "pro_winch")


@dataclass(frozen=True)
class BoatOptions:
    """VR options owned by the player. All on by default (the usual "full pack" setting)."""

    light: bool = True
    heavy: bool = True
    reach: bool = True
    foil: bool = True
    hull: bool = True
    pro_winch: bool = True

    @classmethod
    def from_owned(cls, owned: str) -> BoatOptions:
        """Builds options from a comma-separated list of owned ones, e.g. "foil" or "foil,hull".
        "all" means the full pack, "none" the bare boat (Jib and Spi only)."""
        if owned.strip() == "all":
            return cls()
        names = {name.strip() for name in owned.split(",") if name.strip() and name.strip() != "none"}
        unknown = names - set(OPTION_NAMES)
        if unknown:
            raise ValueError(f"unknown boat option(s): {', '.join(sorted(unknown))} (known: {', '.join(OPTION_NAMES)})")
        return cls(**{name: name in names for name in OPTION_NAMES})

    def allows_sail(self, sail_name: str) -> bool:
        if sail_name in BASE_SAILS:
            return True
        for pack, sails in SAIL_PACKS.items():
            if sail_name in sails:
                return bool(getattr(self, pack))
        return False
