from __future__ import annotations

from sailrouter.service.ensemble_download_job import EnsembleDownloadJob
from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.router_builder import WEATHER_AREA
from sailrouter.weather.forecast_store import ForecastStore
from sailrouter.weather.gefs_query_builder import GEFS_MEMBERS, GefsQueryBuilder
from sailrouter.weather.gefs_run_catalog import GefsRunCatalog
from sailrouter.weather.gefs_run_downloader import GefsRunDownloader
from sailrouter.weather.gfs_run_clock import GfsRunClock
from sailrouter.weather.nomads_client import NomadsClient
from sailrouter.weather.run_download_lock import RunDownloadLock

GEFS_REQUEST_INTERVAL_S = 0.5  # at most 2 requests per second: NOMADS bans abusive clients


def build_ensemble_job(paths: ProjectPaths) -> EnsembleDownloadJob:
    """Wires the GEFS download job on the project's weather cache (shared by the web app and the CLI)."""
    store = ForecastStore(paths.weather_dir)
    catalog = GefsRunCatalog(GfsRunClock(model="gefs"), store, GEFS_MEMBERS)
    client = NomadsClient(min_interval_s=GEFS_REQUEST_INTERVAL_S)
    downloader = GefsRunDownloader(client, GefsQueryBuilder(WEATHER_AREA), store)
    return EnsembleDownloadJob(catalog, downloader, RunDownloadLock(paths.weather_dir))
