from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Body, HTTPException

from sailrouter.course.race_catalog import RaceCatalog, RaceFileError
from sailrouter.domain.race_boat import RaceBoat
from sailrouter.polar.player_polar_reader import InvalidPolarError, PlayerPolarReader
from sailrouter.service.boat_polar_locator import BoatPolarLocator
from sailrouter.service.player_polar_store import PlayerPolarStore
from sailrouter.service.project_paths import ProjectPaths

log = logging.getLogger(__name__)


def polars_router(paths: ProjectPaths) -> APIRouter:
    """The polar a boat sails with: read it (community or player's), import the player's own copy from the game,
    or remove it to go back to the community polar."""
    router = APIRouter(prefix="/api/races/{race_id}/boats/{boat_id}/polar")
    catalog = RaceCatalog(paths.races_dir)
    locator = BoatPolarLocator(paths)
    store = PlayerPolarStore(paths.polars_dir)

    def boat_of(race_id: str, boat_id: str) -> RaceBoat:
        try:
            return catalog.load(race_id).boat(boat_id)
        except (RaceFileError, KeyError) as error:
            raise HTTPException(404, f"unknown race or boat: {race_id}/{boat_id}") from error

    def described(race_id: str, boat: RaceBoat) -> dict:
        """The raw polar (the frontend reads its `winch` block) plus where it comes from."""
        try:
            polar = json.loads(locator.polar_file(race_id, boat).read_text(encoding="utf-8"))
        except ValueError as error:
            raise HTTPException(404, str(error)) from error
        imported = store.imported_at(race_id, boat.id)
        return {**polar, "_source": locator.source(race_id, boat),
                "_imported_at": imported.isoformat().replace("+00:00", "Z") if imported else None}

    @router.get("")
    def polar(race_id: str, boat_id: str) -> dict:
        return described(race_id, boat_of(race_id, boat_id))

    @router.post("")
    def import_polar(race_id: str, boat_id: str, payload: Any = Body(...)) -> dict:
        """The JSON copied from the game's network tab: the raw polar or any response wrapping it."""
        boat = boat_of(race_id, boat_id)
        try:
            polar = PlayerPolarReader().read(payload)
        except InvalidPolarError as error:
            raise HTTPException(400, f"invalid polar: {error}") from error
        store.save(race_id, boat.id, polar)
        log.info("player polar imported for %s/%s (%s)", race_id, boat.id, polar.get("label", "no label"))
        return described(race_id, boat)

    @router.delete("")
    def remove_polar(race_id: str, boat_id: str) -> dict:
        boat = boat_of(race_id, boat_id)
        if store.delete(race_id, boat.id):
            log.info("player polar removed for %s/%s: back to the community polar", race_id, boat.id)
        return described(race_id, boat)

    return router
