from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from sailrouter.api.ensemble_result_builder import EnsembleResultBuilder
from sailrouter.api.ensemble_status_json import ensemble_status_json
from sailrouter.api.route_result_builder import RouteResultBuilder
from sailrouter.api.schemas import RouteRequest
from sailrouter.api.wind_grid_exporter import WindGridExporter
from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.service.ensemble_download_job import EnsembleDownloadJob
from sailrouter.service.ensemble_route_planner import EnsembleRoutePlanner
from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.route_planner import RoutePlanner

ROUTE_HOURS = 120.0
MAP_WIND_HOURS = [0, 4, 8, 12, 16, 24, 48]
MAX_ROUTE_HOURS = 120
log = logging.getLogger(__name__)


def routing_router(paths: ProjectPaths, ensemble_job: EnsembleDownloadJob) -> APIRouter:
    """Route computation, ensemble download status and the map wind. Endpoints are plain `def`: FastAPI runs
    them in a worker thread, so a computation does not block the server.

    `POST /api/route` routes the 31 GEFS members when their run is on disk, otherwise the game's GFS only;
    either way it starts the GEFS download in the background when a newer run should exist."""
    router = APIRouter(prefix="/api")

    @router.post("/route")
    def compute_route(request: RouteRequest) -> dict:
        position = GeoPoint(request.position.lat, request.position.lon)
        try:
            race = RaceCatalog(paths.races_dir).load(request.race_id)
            start = max(race.start_time, datetime.now(UTC))
            gefs_run = ensemble_job.ensure(start, start + timedelta(hours=ROUTE_HOURS))
            arguments = dict(race_id=request.race_id, boat_id=request.boat_id, position=position, hours=ROUTE_HOURS,
                             start=start, options=request.options.to_options(), maneuvers=request.maneuver_timings())
            if gefs_run is not None:
                ensemble = _ensemble_or_none(paths, gefs_run, arguments)
                if ensemble is not None:
                    return EnsembleResultBuilder().build(ensemble, ensemble_job.status())
            report = RoutePlanner(paths).plan(**arguments)
        except (ValueError, KeyError) as error:
            raise HTTPException(400, str(error)) from error
        except (RuntimeError, ConnectionError) as error:
            raise HTTPException(503, str(error)) from error
        return RouteResultBuilder().build(report, ensemble_job.status())

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
            field, run = RoutePlanner(paths).wind_forecast(start, max(max(wanted), 1))
        except (RuntimeError, ConnectionError) as error:
            raise HTTPException(503, str(error)) from error
        return {
            "model": "GFS 0.25°",
            "run": run.cycle.isoformat().replace("+00:00", "Z"),
            "start": start.isoformat().replace("+00:00", "Z"),
            "times": WindGridExporter().export(field, start, wanted),
        }

    return router


def _ensemble_or_none(paths: ProjectPaths, gefs_run, arguments: dict):
    """The ensemble report, or None (logged) when the members cannot be routed, so the game's route is still
    served (e.g. a damaged cached GRIB file)."""
    try:
        return EnsembleRoutePlanner(paths).plan(gefs_run=gefs_run, **arguments)
    except (ValueError, KeyError):
        raise
    except Exception:  # noqa: BLE001 - any failure of the 31 routes must not hide the game's route
        log.exception("ensemble routing failed on %s; serving the GFS route only", gefs_run.key)
        return None


def _parse_hours(text: str) -> list[int]:
    try:
        hours = sorted({int(part) for part in text.split(",") if part.strip()})
    except ValueError as error:
        raise HTTPException(400, f"hours must be whole numbers, e.g. 11 or 11,13 (got {text!r})") from error
    if not hours or hours[0] < 0 or hours[-1] > MAX_ROUTE_HOURS:
        raise HTTPException(400, f"hours must be between 0 and {MAX_ROUTE_HOURS}")
    return hours
