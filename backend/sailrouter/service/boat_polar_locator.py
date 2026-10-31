from __future__ import annotations

from pathlib import Path

from sailrouter.domain.race_boat import RaceBoat
from sailrouter.service.player_polar_store import PlayerPolarStore
from sailrouter.service.project_paths import ProjectPaths

PLAYER = "player"
COMMUNITY = "community"


class BoatPolarLocator:
    """Which polar file a boat sails with: the one the player imported for this race and boat when there is one,
    else the community polar named in the race file."""

    def __init__(self, paths: ProjectPaths) -> None:
        self._paths = paths
        self._store = PlayerPolarStore(paths.polars_dir)

    def source(self, race_id: str, boat: RaceBoat) -> str:
        return PLAYER if self._store.has(race_id, boat.id) else COMMUNITY

    def polar_file(self, race_id: str, boat: RaceBoat) -> Path:
        if self._store.has(race_id, boat.id):
            return self._store.path(race_id, boat.id)
        if boat.polar_path is None:
            raise ValueError(f"no polar available yet for boat {boat.id!r}")
        return self._paths.resolve(boat.polar_path)

    def fingerprint(self, race_id: str, boat: RaceBoat) -> str:
        """Changes whenever the polar used changes (import, re-import, removal): part of the result cache key."""
        imported = self._store.imported_at(race_id, boat.id)
        return f"{PLAYER}@{imported.timestamp():.6f}" if imported else COMMUNITY
