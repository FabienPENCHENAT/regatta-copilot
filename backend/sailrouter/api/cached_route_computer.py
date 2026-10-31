from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from time import perf_counter

from sailrouter.api.ensemble_result_builder import EnsembleResultBuilder
from sailrouter.api.ensemble_status_json import ensemble_status_json
from sailrouter.api.route_request_ledger import RouteRequestLedger
from sailrouter.api.route_result_builder import RouteResultBuilder
from sailrouter.api.route_result_cache import RouteResultCache
from sailrouter.api.schemas import RouteRequest
from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.race import Race
from sailrouter.service.boat_polar_locator import BoatPolarLocator
from sailrouter.service.computation_superseded import ComputationSuperseded
from sailrouter.service.ensemble_download_job import EnsembleDownloadJob
from sailrouter.service.ensemble_route_planner import EnsembleRoutePlanner
from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.route_planner import RoutePlanner
from sailrouter.weather.gfs_run_clock import GfsRunClock
from sailrouter.weather.model_run import ModelRun

ROUTE_HOURS = 120.0
FALLBACK_RESULT_LIFETIME = timedelta(minutes=30)  # result made on an older run than expected: retry soon
ENGINE_VERSION = 6  # bump when the routing, the result format or a race file changes, so stored results are recomputed (6: no Fréhel gate)
log = logging.getLogger(__name__)
_COMPUTING = threading.Lock()  # shared by requests and the background pre-computation
_REQUESTS = RouteRequestLedger()


class CachedRouteComputer:
    """Answers a route request: the stored result when the same inputs were computed on the same weather runs,
    else a fresh computation (the 31 GEFS members when their run is on disk, the game's GFS only otherwise),
    stored for next time. Never waits for a GFS download when a run is on disk (the refresher downloads).
    Shared by `POST /api/route` and the background refresher."""

    def __init__(self, paths: ProjectPaths, ensemble_job: EnsembleDownloadJob,
                 now: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None:
        self._paths = paths
        self._job = ensemble_job
        self._cache = RouteResultCache(paths.results_dir)
        self._now = now

    def window(self, race: Race, now: datetime) -> tuple[datetime, datetime]:
        start = max(race.start_time, now)
        return start, start + timedelta(hours=ROUTE_HOURS)

    def result(self, request: RouteRequest, from_player: bool = True) -> dict:
        """Raises ComputationSuperseded when a newer player request arrives before this one is computed."""
        superseded = _REQUESTS.staleness_check(new_request=from_player)
        now = self._now()
        race = RaceCatalog(self._paths.races_dir).load(request.race_id)
        boat = race.boat(request.boat_id or race.default_boat)
        _check_mark(race, request.next_mark)
        start, end = self.window(race, now)
        gefs_run = self._job.ensure(start, end)
        expected_gfs = GfsRunClock().latest_complete(now)
        gfs_run = RoutePlanner(self._paths).cached_game_run(start, ROUTE_HOURS) or expected_gfs
        polar = BoatPolarLocator(self._paths).fingerprint(race.id, boat)
        key = self._cache.key(_cache_inputs(request, start, gfs_run, gefs_run, polar))
        cached = self._cache.get(key, now)
        if cached is not None:
            return {**cached, "ensemble": ensemble_status_json(self._job.status())}
        # One computation at a time: several at once (clicks in a row, background refresh) fight for the
        # processors and all get slow. Once our turn comes, the same result may already be stored, or the
        # player may have asked for something else meanwhile.
        with _COMPUTING:
            if superseded():
                raise ComputationSuperseded("a newer route request replaced this one")
            cached = self._cache.get(key, now)
            if cached is not None:
                return {**cached, "ensemble": ensemble_status_json(self._job.status())}
            began = perf_counter()
            result = self._compute(request, start, gefs_run, superseded)
            game_run = result["weather"].get("game_run", result["weather"]["run"])
            fell_back = not game_run.startswith(expected_gfs.cycle.strftime("%Y-%m-%dT%H"))
            # Scenarios were on disk but the ensemble failed (logged): keep the GFS-only answer briefly, retry soon.
            fell_back = fell_back or (gefs_run is not None and result["weather"]["member_count"] == 1)
            self._cache.put(key, result, now + FALLBACK_RESULT_LIFETIME if fell_back else None)
            log.info("route %s/%s computed in %.0f s on GFS %s, %s%s", race.id, boat.id, perf_counter() - began,
                     game_run, result["weather"]["model"], " (older GFS run, expires in 30 min)" if fell_back else "")
            return result

    def _compute(self, request: RouteRequest, start: datetime, gefs_run: ModelRun | None,
                 superseded: Callable[[], bool]) -> dict:
        position = GeoPoint(request.position.lat, request.position.lon)
        arguments = dict(race_id=request.race_id, boat_id=request.boat_id, position=position, hours=ROUTE_HOURS,
                         start=start, next_mark=request.next_mark, options=request.options.to_options(),
                         maneuvers=request.maneuver_timings())
        if gefs_run is not None:
            ensemble = self._ensemble_or_none(gefs_run, arguments, superseded)
            if ensemble is not None:
                return EnsembleResultBuilder().build(ensemble, self._job.status())
        report = RoutePlanner(self._paths, prefer_cached=True).plan(**arguments)
        return RouteResultBuilder().build(report, self._job.status())

    def _ensemble_or_none(self, gefs_run: ModelRun, arguments: dict, superseded: Callable[[], bool]):
        """The ensemble report, or None (logged) when the members cannot be routed, so the game's route is still
        served (e.g. a damaged cached GRIB file)."""
        try:
            return EnsembleRoutePlanner(self._paths, prefer_cached=True).plan(
                gefs_run=gefs_run, stop_if=superseded, **arguments)
        except (ValueError, KeyError, ComputationSuperseded):
            raise
        except Exception:  # noqa: BLE001 - any failure of the 31 routes must not hide the game's route
            log.exception("ensemble routing failed on %s; serving the GFS route only", gefs_run.key)
            return None


def _check_mark(race: Race, mark_id: str | None) -> None:
    if mark_id is None:
        return
    known = [mark.id for mark in (*race.marks, race.finish)]
    if mark_id not in known:
        raise ValueError(f"unknown mark {mark_id!r} (known: {', '.join(known)})")


def _cache_inputs(request: RouteRequest, start: datetime, gfs_run: ModelRun, gefs_run: ModelRun | None,
                  polar: str) -> dict:
    """Everything a result depends on. The start is rounded to 30 min, so a race already under way still reuses
    results for a while."""
    rounded = start.replace(minute=start.minute // 30 * 30, second=0, microsecond=0)
    return {
        "engine": ENGINE_VERSION, "race": request.race_id, "boat": request.boat_id,
        "position": [round(request.position.lat, 4), round(request.position.lon, 4)],
        "sails": sorted(request.options.sails), "equipment": [request.options.foil, request.options.hull,
                                                              request.options.pro_winch],
        "maneuvers": {k: v.model_dump() for k, v in request.maneuvers.items()},
        "next_mark": request.next_mark, "polar": polar,
        "start": rounded.isoformat(), "gfs": gfs_run.key, "gefs": gefs_run.key if gefs_run else None,
    }
