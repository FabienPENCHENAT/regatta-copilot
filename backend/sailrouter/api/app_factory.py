from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from sailrouter.api.routes_races import races_router
from sailrouter.api.routes_routing import routing_router
from sailrouter.service.project_paths import ProjectPaths


def create_app(paths: ProjectPaths | None = None) -> FastAPI:
    """The web app: JSON API under /api, and the frontend files served at /.
    Start with `uvicorn sailrouter.api.app_factory:create_app --factory` (see run.sh)."""
    paths = paths or ProjectPaths()
    app = FastAPI(title="Routeur Voile", docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.include_router(races_router(paths))
    app.include_router(routing_router(paths))
    app.mount("/", StaticFiles(directory=paths.root / "frontend", html=True), name="frontend")
    return app
