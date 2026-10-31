from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ProjectPaths:
    """Where the data files and the runtime cache live, relative to the repository root."""

    root: Path = REPO_ROOT

    @property
    def races_dir(self) -> Path:
        return self.root / "races"

    @property
    def land_geojson(self) -> Path:
        return self.root / "frontend" / "map-data" / "land.geojson"

    @property
    def land_cache_dir(self) -> Path:
        """Land rasters derived from the coastline (the coast margin), rebuilt when the coastline changes."""
        return self.root / "var" / "land"

    @property
    def weather_dir(self) -> Path:
        return self.root / "var" / "weather"

    @property
    def results_dir(self) -> Path:
        return self.root / "var" / "results"

    @property
    def polars_dir(self) -> Path:
        """Polars imported by the player (runtime data, git-ignored)."""
        return self.root / "var" / "polars"

    @property
    def last_request_file(self) -> Path:
        return self.root / "var" / "last_request.json"

    @property
    def routes_dir(self) -> Path:
        return self.root / "var" / "routes"

    def resolve(self, relative: str) -> Path:
        return self.root / relative
