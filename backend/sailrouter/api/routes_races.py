from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.service.project_paths import ProjectPaths


def races_router(paths: ProjectPaths) -> APIRouter:
    """Race list and race files (course, zones, boats). Boat polars: `routes_polars.py`."""
    router = APIRouter(prefix="/api/races")
    catalog = RaceCatalog(paths.races_dir)

    @router.get("")
    def list_races() -> list[dict]:
        races = []
        for race_id in catalog.race_ids():
            data = _race_file(paths, race_id)
            races.append({"id": race_id, "boats": [b["id"] for b in data["boats"]], "default_boat": data["default_boat"]})
        return races

    @router.get("/{race_id}")
    def race(race_id: str) -> dict:
        return _race_file(paths, race_id)

    return router


def _race_file(paths: ProjectPaths, race_id: str) -> dict:
    path = paths.races_dir / f"{race_id}.json"
    if not path.is_file() or path.parent != paths.races_dir:
        raise HTTPException(404, f"unknown race {race_id!r}")
    return json.loads(path.read_text(encoding="utf-8"))
