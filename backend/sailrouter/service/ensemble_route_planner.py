from __future__ import annotations

import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime, timedelta
from time import perf_counter

from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.ensemble.ensemble_synthesizer import EnsembleSynthesizer
from sailrouter.polar.boat_options import BoatOptions
from sailrouter.polar.winch_timings import ManeuverTiming
from sailrouter.service import member_routing_worker
from sailrouter.service.ensemble_report import EnsembleReport
from sailrouter.service.member_routing_worker import MemberRoutingSpec
from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.route_planner import RoutePlanner
from sailrouter.weather.gefs_query_builder import GEFS_MEMBERS
from sailrouter.weather.lead_time_plan import LeadTimePlan
from sailrouter.weather.model_run import ModelRun


class EnsembleRoutePlanner:
    """Routes every GEFS member of a run already on disk in parallel worker processes, the deterministic GFS
    (the game's route) in this process meanwhile, then turns the member routes into options."""

    def __init__(self, paths: ProjectPaths, workers: int | None = None) -> None:
        self._paths = paths
        self._workers = workers or max(1, (os.cpu_count() or 2) - 1)

    def plan(
        self, race_id: str, boat_id: str | None, position: GeoPoint, hours: float, gefs_run: ModelRun,
        start: datetime | None = None, options: BoatOptions | None = None,
        maneuvers: dict[str, ManeuverTiming] | None = None, next_mark: str | None = None,
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
            pending = pool.map(member_routing_worker.route_member, GEFS_MEMBERS)
            game = RoutePlanner(self._paths).plan(race_id, boat_id, position, hours, start, next_mark, options, maneuvers)
            member_routes = {member: route for member, route in pending if route is not None}
        routed = perf_counter()
        synthesis = EnsembleSynthesizer().synthesize(member_routes, game.route, game.progress)
        timings = {"members": routed - began, "synthesis": perf_counter() - routed, "total": perf_counter() - began}
        return EnsembleReport(game, gefs_run, member_routes, synthesis, timings)
