from __future__ import annotations

import multiprocessing
import os
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, wait
from datetime import UTC, datetime, timedelta
from time import perf_counter

from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.ensemble.ensemble_synthesizer import EnsembleSynthesizer
from sailrouter.polar.boat_options import BoatOptions
from sailrouter.polar.winch_timings import ManeuverTiming
from sailrouter.service import member_routing_worker
from sailrouter.service.computation_superseded import ComputationSuperseded
from sailrouter.service.ensemble_report import EnsembleReport
from sailrouter.service.member_routing_worker import MemberRoutingSpec
from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.route_planner import RoutePlanner
from sailrouter.weather.gefs_query_builder import GEFS_MEMBERS
from sailrouter.weather.lead_time_plan import LeadTimePlan
from sailrouter.weather.model_run import ModelRun

POLL_S = 0.5  # how often a running ensemble checks whether it was replaced


class EnsembleRoutePlanner:
    """Routes every GEFS member of a run already on disk in parallel worker processes, the deterministic GFS
    (the game's route) in this process meanwhile, then turns the member routes into options. `stop_if` is
    polled while the members run: when it turns true, the members not started yet are cancelled and
    ComputationSuperseded is raised."""

    def __init__(self, paths: ProjectPaths, workers: int | None = None, prefer_cached: bool = False) -> None:
        self._paths = paths
        self._workers = workers or max(1, (os.cpu_count() or 2) - 1)
        self._prefer_cached = prefer_cached  # GFS run: see RoutePlanner

    def plan(
        self, race_id: str, boat_id: str | None, position: GeoPoint, hours: float, gefs_run: ModelRun,
        start: datetime | None = None, options: BoatOptions | None = None,
        maneuvers: dict[str, ManeuverTiming] | None = None, next_mark: str | None = None,
        stop_if: Callable[[], bool] = lambda: False,
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
        timings = {"members": routed - began, "synthesis": perf_counter() - routed, "total": perf_counter() - began}
        return EnsembleReport(game, gefs_run, member_routes, synthesis, timings)


def _abandon(pool: ProcessPoolExecutor) -> None:
    """Drops the members not started yet and stops the running ones at once, so the next request gets the
    processors back immediately (a member takes several seconds). Uses the pool's process table: the public
    API can only wait for running tasks."""
    pool.shutdown(wait=False, cancel_futures=True)
    for process in list((getattr(pool, "_processes", None) or {}).values()):
        process.terminate()
