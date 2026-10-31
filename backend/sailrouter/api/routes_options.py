from __future__ import annotations

from fastapi import APIRouter, HTTPException

from sailrouter.api.schemas import OptionsImpactRequest
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.service.options_impact import OptionsImpact
from sailrouter.service.project_paths import ProjectPaths


def options_router(paths: ProjectPaths) -> APIRouter:
    """`POST /api/options-impact`: miles gained or lost on the game's route by changing boat options (polar page).
    Two GFS routes, a few seconds each."""
    router = APIRouter(prefix="/api")

    @router.post("/options-impact")
    def options_impact(request: OptionsImpactRequest) -> dict:
        try:
            return OptionsImpact(paths).compare(
                request.race_id, request.boat_id, GeoPoint(request.position.lat, request.position.lon),
                request.current.to_options(), request.changed.to_options(), request.maneuver_timings(),
                request.next_mark)
        except (ValueError, KeyError) as error:
            raise HTTPException(400, str(error)) from error
        except (RuntimeError, ConnectionError) as error:
            raise HTTPException(503, str(error)) from error

    return router
