from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sailrouter.domain.exclusion_zone import ExclusionZone
from sailrouter.domain.mark import Mark
from sailrouter.domain.race_boat import RaceBoat


@dataclass(frozen=True)
class Race:
    """A race course: boats with their start line, ordered marks, finish line and forbidden zones."""

    id: str
    name: str
    start_time: datetime
    close_time: datetime
    default_boat: str
    boats: tuple[RaceBoat, ...]
    marks: tuple[Mark, ...]
    finish: Mark
    exclusion_zones: tuple[ExclusionZone, ...]

    def boat(self, boat_id: str) -> RaceBoat:
        for boat in self.boats:
            if boat.id == boat_id:
                return boat
        known = ", ".join(b.id for b in self.boats)
        raise KeyError(f"race {self.id} has no boat {boat_id!r} (known: {known})")

    def mark(self, mark_id: str) -> Mark:
        for mark in (*self.marks, self.finish):
            if mark.id == mark_id:
                return mark
        raise KeyError(f"race {self.id} has no mark {mark_id!r}")
