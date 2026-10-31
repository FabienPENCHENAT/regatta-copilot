from __future__ import annotations

import sys
from datetime import UTC, datetime
from time import perf_counter

from sailrouter.cli.project_paths import ProjectPaths
from sailrouter.cli.route_report import RouteReport
from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.race import Race
from sailrouter.geography.coastline_loader import CoastlineLoader
from sailrouter.geography.land_mask import LandMask
from sailrouter.geography.obstacle_checker import ObstacleChecker
from sailrouter.geography.polygon_rasterizer import PolygonRasterizer
from sailrouter.geography.raster_grid import RasterGrid
from sailrouter.geography.zone_crossing_detector import ZoneCrossingDetector
from sailrouter.polar.boat_options import BoatOptions
from sailrouter.polar.maneuver_penalty import ManeuverPenalty
from sailrouter.polar.speed_model import SpeedModel
from sailrouter.polar.vr_polar_parser import VrPolarParser
from sailrouter.routing.heading_fan import HeadingFan
from sailrouter.routing.isochrone_pruner import IsochronePruner
from sailrouter.routing.isochrone_router import IsochroneRouter
from sailrouter.routing.mark_progress import MarkProgress
from sailrouter.routing.route_tracer import RouteTracer
from sailrouter.routing.time_schedule import TimeSchedule
from sailrouter.weather.forecast_store import ForecastStore
from sailrouter.weather.gfs_query_builder import GfsQueryBuilder
from sailrouter.weather.gfs_run_clock import GfsRunClock
from sailrouter.weather.gfs_run_downloader import GfsRunDownloader
from sailrouter.weather.gfs_wind_source import GfsWindSource
from sailrouter.weather.grib_decoder import GribDecoder
from sailrouter.weather.lead_time_plan import LeadTimePlan
from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.nomads_client import NomadsClient
from sailrouter.weather.weather_area import WeatherArea
from sailrouter.weather.wind_field import WindField

WEATHER_AREA = WeatherArea(south_deg=0.0, north_deg=60.0, west_deg=-80.0, east_deg=10.0)
LAND_RESOLUTION_DEG = 0.005  # ≈ 550 m × 370 m at 48°N: keeps the 1 nm wide Fréhel gate open


class RouteCommand:
    """Routes one boat on the deterministic GFS: builds every object (the only place that knows all layers),
    runs the router and returns a `RouteReport`."""

    def __init__(self, paths: ProjectPaths) -> None:
        self._paths = paths
        self._timings: dict[str, float] = {}

    def execute(
        self, race_id: str, boat_id: str | None, position: GeoPoint, hours: float,
        start: datetime | None = None, next_mark: str | None = None, options: BoatOptions | None = None,
    ) -> RouteReport:
        clock_start = perf_counter()
        now = datetime.now(UTC)
        race = RaceCatalog(self._paths.races_dir).load(race_id)
        boat = race.boat(boat_id or race.default_boat)
        if boat.polar_path is None:
            raise ValueError(f"no polar available yet for boat {boat.id!r}")
        schedule = TimeSchedule(start or max(race.start_time, now), hours)
        clock = GfsRunClock()
        wind, run = self._timed("weather", lambda: self._wind_field(clock, schedule, now))
        speed_model, penalty = self._timed("polar", lambda: self._boat_models(boat.polar_path, options or BoatOptions()))
        obstacles = self._timed("land", lambda: self._obstacles(race))
        progress = MarkProgress.from_race(race, position, first_mark_id=next_mark)
        router = IsochroneRouter(wind, speed_model, penalty, obstacles, HeadingFan(5.0), IsochronePruner(0.5))
        fronts = self._timed("routing", lambda: router.run(position, schedule, progress))
        route = RouteTracer(speed_model.sail_names).trace(fronts, progress)
        self._timings["total"] = perf_counter() - clock_start
        return RouteReport(
            race.id, race.name, boat.id, position, now, run, clock.next_expected(run), progress, route,
            len(fronts) - 1, dict(self._timings),
        )

    def _timed(self, name: str, action):
        began = perf_counter()
        result = action()
        self._timings[name] = perf_counter() - began
        return result

    def _wind_field(self, clock: GfsRunClock, schedule: TimeSchedule, now: datetime) -> tuple[WindField, ModelRun]:
        store = ForecastStore(self._paths.weather_dir)
        downloader = GfsRunDownloader(NomadsClient(), GfsQueryBuilder(WEATHER_AREA), store)
        source = GfsWindSource(clock, LeadTimePlan(), downloader, store, GribDecoder())
        return source.wind_field(schedule.start, schedule.end, now, _print_download_progress)

    def _boat_models(self, polar_path: str, options: BoatOptions) -> tuple[SpeedModel, ManeuverPenalty]:
        vr_polar = VrPolarParser().load(self._paths.resolve(polar_path))
        return SpeedModel(vr_polar, options), ManeuverPenalty(vr_polar.winch, pro_winch=options.pro_winch)

    def _obstacles(self, race: Race) -> ObstacleChecker:
        area = WEATHER_AREA
        grid = RasterGrid(area.south_deg, area.west_deg, area.north_deg, area.east_deg, LAND_RESOLUTION_DEG)
        polygons = CoastlineLoader().load(self._paths.land_geojson)
        land = LandMask(grid, PolygonRasterizer(grid).rasterize(polygons))
        return ObstacleChecker(land, ZoneCrossingDetector(race.exclusion_zones))


def _print_download_progress(done: int, total: int) -> None:
    print(f"\rDownloading GFS: {done}/{total} files", end="" if done < total else "\n", file=sys.stderr, flush=True)
