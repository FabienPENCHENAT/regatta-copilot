from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from time import perf_counter

from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.route_report import RouteReport
from sailrouter.service.router_builder import WEATHER_AREA, RouterBuilder
from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.polar.boat_options import BoatOptions
from sailrouter.polar.winch_timings import ManeuverTiming
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
from sailrouter.weather.wind_field import WindField


class RoutePlanner:
    """Routes one boat on the deterministic GFS (the game's weather): loads the race, the weather and the boat,
    runs the router and returns a `RouteReport`. Used by the command line, the web API and the ensemble planner."""

    def __init__(self, paths: ProjectPaths, on_download: Callable[[int, int], None] | None = None) -> None:
        self._paths = paths
        self._on_download = on_download
        self._builder = RouterBuilder(paths)
        self._timings: dict[str, float] = {}

    def wind_forecast(self, start: datetime, hours: float) -> tuple[WindField, ModelRun]:
        """The GFS wind over [start, start + hours], downloaded once per run (for the map)."""
        return self._wind_field(GfsRunClock(), TimeSchedule(start, hours), datetime.now(UTC))

    def plan(
        self, race_id: str, boat_id: str | None, position: GeoPoint, hours: float,
        start: datetime | None = None, next_mark: str | None = None, options: BoatOptions | None = None,
        maneuvers: dict[str, ManeuverTiming] | None = None,
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
        speed_model, penalty = self._timed(
            "polar", lambda: self._builder.boat_models(boat.polar_path, options or BoatOptions(), maneuvers or {}))
        obstacles = self._timed("land", lambda: self._builder.obstacles(race))
        progress = MarkProgress.from_race(race, position, first_mark_id=next_mark)
        router = self._builder.router(wind, speed_model, penalty, obstacles)
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
        return source.wind_field(schedule.start, schedule.end, now, self._on_download or _silent)


def _silent(done: int, total: int) -> None:
    pass
