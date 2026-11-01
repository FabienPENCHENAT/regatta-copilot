"""Code run inside the worker processes that route the GEFS members in parallel.

`initialize` builds, once per process, everything that does not depend on the member (race, polar, land
raster); `route_member` then decodes one member's wind from the cache and routes it; `follow_tracks` sails the
options' tracks in one member's wind (cross-evaluation). Module-level functions because process pools can only
call picklable, importable functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.polar.boat_options import BoatOptions
from sailrouter.polar.winch_timings import ManeuverTiming
from sailrouter.routing.isochrone_router import RoutingError
from sailrouter.routing.mark_progress import MarkProgress
from sailrouter.routing.route import Route
from sailrouter.routing.route_tracer import RouteTracer
from sailrouter.routing.time_schedule import TimeSchedule
from sailrouter.routing.track_follower import TrackFollower
from sailrouter.service.boat_polar_locator import BoatPolarLocator
from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.router_builder import RouterBuilder
from sailrouter.weather.forecast_store import ForecastStore
from sailrouter.weather.gefs_member_loader import GefsMemberLoader
from sailrouter.weather.grib_decoder import GribDecoder
from sailrouter.weather.model_run import ModelRun


@dataclass(frozen=True)
class MemberRoutingSpec:
    """Everything a worker needs to route any member of one request (picklable)."""

    root: Path
    race_id: str
    boat_id: str
    position: GeoPoint
    start: datetime
    hours: float
    next_mark: str | None
    options: BoatOptions
    maneuvers: dict[str, ManeuverTiming]
    run: ModelRun
    lead_hours: tuple[int, ...]


_state: dict = {}


def initialize(spec: MemberRoutingSpec) -> None:
    paths = ProjectPaths(spec.root)
    builder = RouterBuilder(paths)
    race = RaceCatalog(paths.races_dir).load(spec.race_id)
    polar_file = BoatPolarLocator(paths).polar_file(race.id, race.boat(spec.boat_id))
    speed_model, penalty = builder.boat_models(polar_file, spec.options, spec.maneuvers)
    _state.update(
        spec=spec, builder=builder, speed_model=speed_model, penalty=penalty, obstacles=builder.obstacles(race),
        progress=MarkProgress.from_race(race, spec.position, first_mark_id=spec.next_mark),
        loader=GefsMemberLoader(ForecastStore(paths.weather_dir), GribDecoder()),
    )


def route_member(member: str) -> tuple[str, Route | None]:
    """The member's best route, or None when it cannot be routed (every heading blocked...)."""
    spec: MemberRoutingSpec = _state["spec"]
    wind = _state["loader"].wind_field(spec.run, member, spec.lead_hours)
    router = _state["builder"].router(wind, _state["speed_model"], _state["penalty"], _state["obstacles"])
    try:
        fronts = router.run(spec.position, TimeSchedule(spec.start, spec.hours), _state["progress"])
    except RoutingError:
        return member, None
    return member, RouteTracer(_state["speed_model"].sail_names).trace(fronts, _state["progress"])


OUTLOOK_HOURS = (48.0, 120.0)


def follow_tracks(member: str, tracks: list[list[tuple[float, float, int]]]) -> tuple[str, list[dict[float, float]]]:
    """Distance to go at +48 h and at the end, for each option's track sailed in this member's wind."""
    spec: MemberRoutingSpec = _state["spec"]
    wind = _state["loader"].wind_field(spec.run, member, spec.lead_hours)
    follower = TrackFollower(_state["speed_model"], _state["progress"])
    hours = sorted({min(hour, spec.hours) for hour in OUTLOOK_HOURS})
    return member, [follower.distances_to_go(track, wind, spec.start, hours) for track in tracks]
