from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from time import perf_counter

from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.polar.boat_options import BoatOptions
from sailrouter.polar.winch_timings import ManeuverTiming
from sailrouter.routing.mark_progress import MarkProgress
from sailrouter.routing.route_tracer import RouteTracer
from sailrouter.routing.time_schedule import TimeSchedule
from sailrouter.service.boat_polar_locator import BoatPolarLocator
from sailrouter.service.gfs_source_factory import build_gfs_source
from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.route_report import RouteReport
from sailrouter.service.router_builder import RouterBuilder
from sailrouter.weather.gfs_run_clock import GfsRunClock
from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.wind_field import WindField


class RoutePlanner:
    """Routes one boat on the deterministic GFS (the game's weather): loads the race, the weather and the boat,
    runs the router and returns a `RouteReport`. Used by the command line, the web API and the ensemble planner.

    `prefer_cached` (web app): route on the newest GFS run already on disk for the window, since the background
    refresher downloads new runs; the command line downloads the latest run itself."""

    def __init__(self, paths: ProjectPaths, on_download: Callable[[int, int], None] | None = None,
                 prefer_cached: bool = False) -> None:
        self._paths = paths
        self._on_download = on_download
        self._prefer_cached = prefer_cached
        self._builder = RouterBuilder(paths)
        self._timings: dict[str, float] = {}

    def wind_forecast(self, start: datetime, hours: float) -> tuple[WindField, ModelRun]:
        """The GFS wind over [start, start + hours], downloaded once per run (for the map)."""
        schedule = TimeSchedule(start, hours)
        return self._wind_field(schedule, datetime.now(UTC))

    def cached_game_run(self, start: datetime, hours: float) -> ModelRun | None:
        """The GFS run a request would route on without downloading, or None when none is on disk."""
        return build_gfs_source(self._paths).cached_run(start, start + timedelta(hours=hours), datetime.now(UTC))

    def plan(
        self, race_id: str, boat_id: str | None, position: GeoPoint, hours: float,
        start: datetime | None = None, next_mark: str | None = None, options: BoatOptions | None = None,
        maneuvers: dict[str, ManeuverTiming] | None = None,
    ) -> RouteReport:
        clock_start = perf_counter()
        now = datetime.now(UTC)
        race = RaceCatalog(self._paths.races_dir).load(race_id)
        boat = race.boat(boat_id or race.default_boat)
        polar_file = BoatPolarLocator(self._paths).polar_file(race.id, boat)
        schedule = TimeSchedule(start or max(race.start_time, now), hours)
        wind, run = self._timed("weather", lambda: self._wind_field(schedule, now))
        speed_model, penalty = self._timed(
            "polar", lambda: self._builder.boat_models(polar_file, options or BoatOptions(), maneuvers or {}))
        obstacles = self._timed("land", lambda: self._builder.obstacles(race))
        progress = MarkProgress.from_race(race, position, first_mark_id=next_mark)
        router = self._builder.router(wind, speed_model, penalty, obstacles)
        fronts = self._timed("routing", lambda: router.run(position, schedule, progress))
        route = RouteTracer(speed_model.sail_names).trace(fronts, progress)
        self._timings["total"] = perf_counter() - clock_start
        return RouteReport(
            race.id, race.name, boat.id, position, now, run, GfsRunClock().next_expected(run), progress, route,
            len(fronts) - 1, dict(self._timings), next_mark_auto=next_mark is None,
        )

    def _timed(self, name: str, action):
        began = perf_counter()
        result = action()
        self._timings[name] = perf_counter() - began
        return result

    def _wind_field(self, schedule: TimeSchedule, now: datetime) -> tuple[WindField, ModelRun]:
        source = build_gfs_source(self._paths)
        return source.wind_field(schedule.start, schedule.end, now, self._on_download or _silent,
                                 prefer_cached=self._prefer_cached)


def _silent(done: int, total: int) -> None:
    pass
