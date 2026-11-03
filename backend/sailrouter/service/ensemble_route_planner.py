from __future__ import annotations

import multiprocessing
import os
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, wait
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from time import perf_counter

from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.ensemble.ensemble_synthesizer import EnsembleSynthesizer
from sailrouter.ensemble.route_option import EnsembleSynthesis
from sailrouter.polar.boat_options import BoatOptions
from sailrouter.polar.winch_timings import ManeuverTiming
from sailrouter.routing.mark_progress import MarkProgress
from sailrouter.routing.route import Route
from sailrouter.service import member_routing_worker
from sailrouter.service.computation_superseded import ComputationSuperseded
from sailrouter.service.ensemble_report import EnsembleReport
from sailrouter.service.member_routing_worker import MemberRoutingSpec
from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.route_planner import RoutePlanner
from sailrouter.service.route_report import RouteReport
from sailrouter.weather.gefs_query_builder import GEFS_MEMBERS
from sailrouter.weather.lead_time_plan import LeadTimePlan
from sailrouter.weather.model_run import ModelRun

POLL_S = 0.5  # how often a running ensemble checks whether it was replaced
GAME_ROUTE = "gfs"  # representative of the option the game's route falls in: that route itself


class EnsembleRoutePlanner:
    """Routes every GEFS member of a run already on disk in parallel worker processes, the deterministic GFS
    (the game's route) in this process meanwhile, then turns the member routes into options, shows each option
    in the game's weather (the GFS route for the option it falls in, the other tracks sailed in the GFS wind:
    what the player is told to set is what the game will give), and sails every option's track in every
    member's weather, plus the player's current route when given (the rest of the
    option followed since the previous computation, from the position). `stop_if` is polled while the members
    run: when it turns true, the members not started yet are cancelled and ComputationSuperseded is raised."""

    def __init__(self, paths: ProjectPaths, workers: int | None = None, prefer_cached: bool = False) -> None:
        self._paths = paths
        self._workers = workers or max(1, (os.cpu_count() or 2) - 1)
        self._prefer_cached = prefer_cached  # GFS run: see RoutePlanner

    def plan(
        self, race_id: str, boat_id: str | None, position: GeoPoint, hours: float, gefs_run: ModelRun,
        start: datetime | None = None, options: BoatOptions | None = None,
        maneuvers: dict[str, ManeuverTiming] | None = None, next_mark: str | None = None,
        stop_if: Callable[[], bool] = lambda: False, current_route: list[tuple[float, float]] | None = None,
    ) -> EnsembleReport:
        began = perf_counter()
        race = RaceCatalog(self._paths.races_dir).load(race_id)
        boat_id = boat_id or race.default_boat
        start = start or max(race.start_time, datetime.now(UTC))
        options, maneuvers = options or BoatOptions(), maneuvers or {}
        leads = LeadTimePlan.gefs().lead_hours_covering(
            gefs_run.hours_since_cycle(start), gefs_run.hours_since_cycle(start + timedelta(hours=hours)))
        spec = MemberRoutingSpec(self._paths.root, race_id, boat_id, position, start, hours, next_mark, options,
                                 maneuvers, gefs_run, tuple(leads))
        context = multiprocessing.get_context("spawn")  # fork is unsafe in a threaded web server
        with ProcessPoolExecutor(min(self._workers, len(GEFS_MEMBERS)), mp_context=context,
                                 initializer=member_routing_worker.initialize, initargs=(spec,)) as pool:
            pending = [pool.submit(member_routing_worker.route_member, member) for member in GEFS_MEMBERS]
            game = RoutePlanner(self._paths, prefer_cached=self._prefer_cached).plan(
                race_id, boat_id, position, hours, start, next_mark, options, maneuvers)
            while wait(pending, timeout=POLL_S).not_done:
                if stop_if():
                    _abandon(pool)
                    raise ComputationSuperseded("a newer route request replaced this one")
            member_routes = {member: route for member, route in (f.result() for f in pending) if route is not None}
            routed = perf_counter()
            synthesis = EnsembleSynthesizer().synthesize(member_routes, game.route, game.progress)
            synthesis = self._in_game_weather(pool, synthesis, game, stop_if)
            synthesized = perf_counter()
            tracks = [_track(option.route) for option in synthesis.options]
            if current_route:
                tracks.append(_current_track(position, current_route, game.progress))
            outlook = self._cross_evaluate(pool, tracks, list(member_routes), stop_if)
        timings = {"members": routed - began, "synthesis": synthesized - routed,
                   "cross": perf_counter() - synthesized, "total": perf_counter() - began}
        options_outlook = outlook[:len(synthesis.options)]
        current_outlook = outlook[len(synthesis.options)] if current_route else None
        return EnsembleReport(game, gefs_run, member_routes, synthesis, timings, options_outlook, current_outlook)

    @staticmethod
    def _in_game_weather(pool: ProcessPoolExecutor, synthesis: EnsembleSynthesis, game: RouteReport,
                         stop_if: Callable[[], bool]) -> EnsembleSynthesis:
        """The options with the routes shown to the player in the game's GFS weather; the members still give
        the options, their probabilities and confidence."""
        others = [option for option in synthesis.options if not option.game_route]
        pending = pool.submit(member_routing_worker.sail_in_game_weather, game.weather_run,
                              [_track(option.route) for option in others])
        while wait([pending], timeout=POLL_S).not_done:
            if stop_if():
                _abandon(pool)
                raise ComputationSuperseded("a newer route request replaced this one")
        sailed = dict(zip((option.id for option in others), pending.result()))
        options = tuple(
            replace(option, representative=GAME_ROUTE, route=game.route) if option.game_route
            else replace(option, route=sailed[option.id])
            for option in synthesis.options
        )
        return replace(synthesis, options=options)

    @staticmethod
    def _cross_evaluate(pool: ProcessPoolExecutor, tracks: list[list[tuple[float, float, int]]], members: list[str],
                        stop_if: Callable[[], bool]) -> list[dict[str, dict[float, float]]]:
        """Every track sailed in every member's wind: outlook[track][member] = {hour: distance to go}."""
        pending = [pool.submit(member_routing_worker.follow_tracks, member, tracks) for member in members]
        while wait(pending, timeout=POLL_S).not_done:
            if stop_if():
                _abandon(pool)
                raise ComputationSuperseded("a newer route request replaced this one")
        outlook: list[dict[str, dict[float, float]]] = [{} for _ in tracks]
        for member, per_option in (future.result() for future in pending):
            for index, distances in enumerate(per_option):
                outlook[index][member] = distances
        return outlook


def _track(route: Route) -> list[tuple[float, float, int]]:
    return [(point.lat_deg, point.lon_deg, point.marks_passed) for point in route.points]


def _current_track(position: GeoPoint, route: list[tuple[float, float]],
                   progress: MarkProgress) -> list[tuple[float, float, int]]:
    """The player's current route from the position, with the marks passed along it."""
    lat = [position.lat_deg, *(point[0] for point in route)]
    lon = [position.lon_deg, *(point[1] for point in route)]
    return list(zip(lat, lon, progress.legs_along(lat, lon)))


def _abandon(pool: ProcessPoolExecutor) -> None:
    """Drops the members not started yet and stops the running ones at once, so the next request gets the
    processors back immediately (a member takes several seconds). Uses the pool's process table: the public
    API can only wait for running tasks."""
    pool.shutdown(wait=False, cancel_futures=True)
    for process in list((getattr(pool, "_processes", None) or {}).values()):
        process.terminate()
