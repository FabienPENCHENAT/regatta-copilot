import math

import numpy as np
import pytest

from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.great_circle import GreatCircle
from sailrouter.routing.course_leg import CourseLeg
from sailrouter.routing.isochrone_router import RoutingError
from sailrouter.routing.mark_progress import MarkProgress
from sailrouter.routing.route_tracer import RouteTracer
from sailrouter.routing.time_schedule import TimeSchedule

from .conftest import BOAT_SPEED_KN, T0, obstacles


def route_to(router, start: GeoPoint, target: GeoPoint, hours: float, radius_nm: float = 1.0):
    progress = MarkProgress([CourseLeg("target", start, target, radius_nm=radius_nm)])
    fronts = router.run(start, TimeSchedule(T0, hours), progress)
    return RouteTracer(("Jib",)).trace(fronts, progress)


def test_upwind_progress_is_the_best_vmg(make_router):
    start, target = GeoPoint(50.0, -10.0), GeoPoint(58.0, -10.0)  # dead upwind (wind from 0°)
    route = route_to(make_router(), start, target, hours=12)
    gained_nm = GreatCircle.distance_nm(50.0, -10.0, 58.0, -10.0) - route.distance_to_go_nm
    assert gained_nm == pytest.approx(12 * BOAT_SPEED_KN * math.cos(math.radians(45)), rel=0.01)
    first = route.points[0]
    assert abs(first.twa_deg) == pytest.approx(45.0)
    assert first.heading_deg in (45.0, 315.0)


def test_beam_reach_goes_straight(make_router):
    start, target = GeoPoint(50.0, -10.0), GeoPoint(50.0, -2.0)
    route = route_to(make_router(), start, target, hours=6)
    end = route.points[-1]
    assert GreatCircle.distance_nm(50.0, -10.0, end.lat_deg, end.lon_deg) == pytest.approx(60.0, rel=0.005)
    assert route.points[0].twa_deg == pytest.approx(-90.0, abs=5.0)  # wind on port side
    assert len(route.points) == 7  # start + 6 hourly steps


def test_reaches_the_target_and_stops(make_router):
    start, target = GeoPoint(50.0, -10.0), GeoPoint(50.0, -9.0)  # 38.6 nm east
    route = route_to(make_router(), start, target, hours=24)
    assert route.finished
    assert route.points[-1].time == T0.replace(hour=16)  # 4 steps of 10 nm


def test_goes_around_an_island(make_router):
    start, target = GeoPoint(48.1, -3.6), GeoPoint(48.1, -2.6)  # island 48.0–48.2°N, 3.2–3.0°W in between
    route = route_to(make_router(with_island=True), start, target, hours=8)
    assert route.finished
    lat = np.array([p.lat_deg for p in route.points])
    lon = np.array([p.lon_deg for p in route.points])
    assert not obstacles(with_island=True).blocked(lat[:-1], lon[:-1], lat[1:], lon[1:]).any()
    assert (lat > 48.2).any() or (lat < 48.0).any()  # had to leave the island's latitudes


def test_tack_penalty_slows_the_beat(make_router):
    start, target = GeoPoint(50.0, -10.0), GeoPoint(58.0, -10.0)
    free = route_to(make_router(), start, target, hours=12)
    costly = route_to(make_router(tack_loss_s=1800), start, target, hours=12)
    assert costly.distance_to_go_nm > free.distance_to_go_nm


def test_start_on_land_is_refused(make_router):
    with pytest.raises(RoutingError):
        route_to(make_router(with_island=True), GeoPoint(48.05, -3.15), GeoPoint(48.1, -2.6), hours=2)
