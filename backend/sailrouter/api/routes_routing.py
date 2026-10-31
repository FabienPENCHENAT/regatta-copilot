from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from sailrouter.api.cached_route_computer import ROUTE_HOURS, CachedRouteComputer
from sailrouter.api.ensemble_status_json import ensemble_status_json
from sailrouter.api.last_route_request_store import LastRouteRequestStore
from sailrouter.api.schemas import RouteRequest
from sailrouter.api.wind_grid_exporter import WindGridExporter
from sailrouter.service.computation_superseded import ComputationSuperseded
from sailrouter.service.ensemble_download_job import EnsembleDownloadJob
from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.route_planner import RoutePlanner

MAP_WIND_HOURS = [0, 4, 8, 12, 16, 24, 48]
MAX_ROUTE_HOURS = int(ROUTE_HOURS)
log = logging.getLogger(__name__)


def routing_router(paths: ProjectPaths, ensemble_job: EnsembleDownloadJob, computer: CachedRouteComputer,
                   last_requests: LastRouteRequestStore) -> APIRouter:
    """Route computation, ensemble download status and the map wind. Endpoints are plain `def`: FastAPI runs
    them in a worker thread, so a computation does not block the server.

    `POST /api/route` routes the 31 GEFS members when their run is on disk, otherwise the game's GFS only;
    either way it starts the GEFS download in the background when a newer run should exist. The request is
    remembered so the background refresher can compute it again when the weather changes."""
    router = APIRouter(prefix="/api")

    @router.post("/route")
    def compute_route(request: RouteRequest) -> dict:
        """Same inputs and same weather runs as an earlier request: the stored result, instantly."""
        try:
            result = computer.result(request)
        except ComputationSuperseded as error:  # the page only shows the answer to its latest request anyway
            raise HTTPException(409, str(error)) from error
        except (ValueError, KeyError) as error:
            raise HTTPException(400, str(error)) from error
        except (RuntimeError, ConnectionError) as error:
            raise HTTPException(503, str(error)) from error
        last_requests.save(request)
        return result

    @router.get("/ensemble/status")
    def ensemble_status() -> dict:
        return ensemble_status_json(ensemble_job.status())

    @router.get("/wind")
    def wind(
        start: datetime = Query(..., description="route start, ISO 8601 UTC"),
        hours: str | None = Query(None, description="comma-separated hours after start, e.g. 11 or 11,13"),
    ) -> dict:
        wanted = _parse_hours(hours) if hours else MAP_WIND_HOURS
        try:
            field, run = RoutePlanner(paths, prefer_cached=True).wind_forecast(start, max(max(wanted), 1))
        except (RuntimeError, ConnectionError) as error:
            raise HTTPException(503, str(error)) from error
        return {
            "model": "GFS 0.25°",
            "run": run.cycle.isoformat().replace("+00:00", "Z"),
            "start": start.isoformat().replace("+00:00", "Z"),
            "times": WindGridExporter().export(field, start, wanted),
        }

    return router


def _parse_hours(text: str) -> list[int]:
    try:
        hours = sorted({int(part) for part in text.split(",") if part.strip()})
    except ValueError as error:
        raise HTTPException(400, f"hours must be whole numbers, e.g. 11 or 11,13 (got {text!r})") from error
    if not hours or hours[0] < 0 or hours[-1] > MAX_ROUTE_HOURS:
        raise HTTPException(400, f"hours must be between 0 and {MAX_ROUTE_HOURS}")
    return hours
