from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from sailrouter.api.route_result_builder import RouteResultBuilder
from sailrouter.api.schemas import RouteRequest
from sailrouter.api.wind_grid_exporter import WindGridExporter
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.route_planner import RoutePlanner

ROUTE_HOURS = 120.0
MAP_WIND_HOURS = [0, 4, 8, 12, 16, 24, 48]


def routing_router(paths: ProjectPaths) -> APIRouter:
    """Route computation and the map wind. Endpoints are plain `def`: FastAPI runs them in a worker thread,
    so a computation does not block the server."""
    router = APIRouter(prefix="/api")

    @router.post("/route")
    def compute_route(request: RouteRequest) -> dict:
        position = GeoPoint(request.position.lat, request.position.lon)
        try:
            report = RoutePlanner(paths).plan(
                request.race_id, request.boat_id, position, ROUTE_HOURS,
                options=request.options.to_options(), maneuvers=request.maneuver_timings(),
            )
        except (ValueError, KeyError) as error:
            raise HTTPException(400, str(error)) from error
        except (RuntimeError, ConnectionError) as error:
            raise HTTPException(503, str(error)) from error
        return RouteResultBuilder().build(report)

    @router.get("/wind")
    def wind(start: datetime = Query(..., description="route start, ISO 8601 UTC")) -> dict:
        try:
            field, run = RoutePlanner(paths).wind_forecast(start, max(MAP_WIND_HOURS))
        except (RuntimeError, ConnectionError) as error:
            raise HTTPException(503, str(error)) from error
        return {
            "model": "GFS 0.25°",
            "run": run.cycle.isoformat().replace("+00:00", "Z"),
            "start": start.isoformat().replace("+00:00", "Z"),
            "times": WindGridExporter().export(field, start, MAP_WIND_HOURS),
        }

    return router
