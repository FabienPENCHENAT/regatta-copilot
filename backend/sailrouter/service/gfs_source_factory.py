from __future__ import annotations

from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.router_builder import WEATHER_AREA
from sailrouter.weather.forecast_store import ForecastStore
from sailrouter.weather.gfs_query_builder import GfsQueryBuilder
from sailrouter.weather.gfs_run_clock import GfsRunClock
from sailrouter.weather.gfs_run_downloader import GfsRunDownloader
from sailrouter.weather.gfs_wind_source import GfsWindSource
from sailrouter.weather.grib_decoder import GribDecoder
from sailrouter.weather.lead_time_plan import LeadTimePlan
from sailrouter.weather.nomads_client import NomadsClient


def build_gfs_source(paths: ProjectPaths) -> GfsWindSource:
    """Wires the deterministic GFS source on the project's weather cache (planner, map wind, refresher)."""
    store = ForecastStore(paths.weather_dir)
    downloader = GfsRunDownloader(NomadsClient(), GfsQueryBuilder(WEATHER_AREA), store)
    return GfsWindSource(GfsRunClock(), LeadTimePlan.game(), downloader, store, GribDecoder())
