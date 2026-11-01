from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from sailrouter.api.cached_route_computer import CachedRouteComputer
from sailrouter.api.last_route_precomputer import LastRoutePrecomputer
from sailrouter.api.last_route_request_store import LastRouteRequestStore
from sailrouter.api.routes_options import options_router
from sailrouter.api.routes_polars import polars_router
from sailrouter.api.routes_races import races_router
from sailrouter.api.routes_routing import routing_router
from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.service.ensemble_download_job import EnsembleDownloadJob
from sailrouter.service.ensemble_job_factory import build_ensemble_job
from sailrouter.service.gfs_source_factory import build_gfs_source
from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.weather_refresher import WeatherRefresher


def create_app(paths: ProjectPaths | None = None, ensemble_job: EnsembleDownloadJob | None = None,
               refresh_in_background: bool = True) -> FastAPI:
    """The web app: JSON API under /api, and the frontend files served at /.
    Start with `uvicorn sailrouter.api.app_factory:create_app --factory` (see run.sh).

    With `refresh_in_background` (off in tests), a `WeatherRefresher` thread runs while the app is up: it
    downloads new GFS/GEFS runs and pre-computes the last route request."""
    paths = paths or ProjectPaths()
    ensemble_job = ensemble_job or build_ensemble_job(paths)
    computer = CachedRouteComputer(paths, ensemble_job)
    last_requests = LastRouteRequestStore(paths.last_request_file)
    precomputer = LastRoutePrecomputer(last_requests, computer, RaceCatalog(paths.races_dir))
    refresher = WeatherRefresher(build_gfs_source(paths), ensemble_job, precomputer.window, precomputer.precompute)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if refresh_in_background:
            _show_info_logs()
            refresher.start()
        yield
        refresher.stop()

    app = FastAPI(title="Regatta Copilot", docs_url="/api/docs", openapi_url="/api/openapi.json", lifespan=lifespan)
    app.include_router(races_router(paths))
    app.include_router(polars_router(paths))
    app.include_router(options_router(paths))
    app.include_router(routing_router(paths, ensemble_job, computer, last_requests))
    app.mount("/", StaticFiles(directory=paths.root / "frontend", html=True), name="frontend")
    return app


def _show_info_logs() -> None:
    """uvicorn only configures its own loggers: print the app's INFO messages too (downloads, pre-computing)."""
    logger = logging.getLogger("sailrouter")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
