"""Routing around Guadeloupe on the real coastline, zones and race file, with a synthetic trade wind (no network)."""

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.polar.boat_options import BoatOptions
from sailrouter.routing.mark_progress import MarkProgress
from sailrouter.routing.route_tracer import RouteTracer
from sailrouter.routing.time_schedule import TimeSchedule
from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.router_builder import RouterBuilder
from sailrouter.weather.wind_field import WindField
from sailrouter.weather.wind_grid import WindGrid

T0 = datetime(2026, 11, 12, tzinfo=UTC)


def trade_wind(from_deg: float = 80.0, speed_kn: float = 15.0) -> WindField:
    lat, lon = np.arange(10.0, 25.25, 0.25), np.arange(-70.0, -54.75, 0.25)
    speed_ms = speed_kn / 1.943844
    u = np.full((lat.size, lon.size), -speed_ms * np.sin(np.radians(from_deg)), np.float32)
    v = np.full_like(u, -speed_ms * np.cos(np.radians(from_deg)))
    return WindField([WindGrid(T0 + timedelta(hours=h), lat, lon, u, v) for h in (0, 240)])


@pytest.fixture(scope="module")
def world():
    paths = ProjectPaths()
    race = RaceCatalog(paths.races_dir).load("route-du-rhum-2026")
    builder = RouterBuilder(paths)
    speed, penalty = builder.boat_models(paths.resolve(race.boat("class40").polar_path), BoatOptions(), {})
    return race, builder, speed, penalty, builder.obstacles(race)


def route_from(world, start: GeoPoint, first_mark: str | None):
    race, builder, speed, penalty, obstacles = world
    progress = MarkProgress.from_race(race, start, first_mark_id=first_mark)
    fronts = builder.router(trade_wind(), speed, penalty, obstacles).run(start, TimeSchedule(T0, 48), progress)
    return RouteTracer(speed.sail_names).trace(fronts, progress), progress


def test_from_the_east_the_route_rounds_guadeloupe_to_port_and_finishes(world):
    route, progress = route_from(world, GeoPoint(17.0, -60.0), None)
    assert [leg.mark_id for leg in progress.legs][0] == "tete_anglais"
    assert route.finished
    passed = [next(p for p in route.points if p.marks_passed > k) for k in range(len(progress.legs))]
    assert [p.time for p in passed] == sorted(p.time for p in passed)
    tete = next(i for i, p in enumerate(route.points) if p.marks_passed > 0)
    before, after = route.points[tete - 1], route.points[tete]
    t = (before.lat_deg - 16.380833) / (before.lat_deg - after.lat_deg)
    assert before.lon_deg + t * (after.lon_deg - before.lon_deg) < -61.764  # crossed west of the islet
    assert route.points[-1].lat_deg == pytest.approx(16.2)  # stops on the finish line


def test_an_explicit_next_mark_skips_the_marks_before_it(world):
    route, progress = route_from(world, GeoPoint(16.2, -61.85), "basse_terre_buoy")
    assert [leg.mark_id for leg in progress.legs] == [
        "basse_terre_buoy", "les_saintes", "pointe_a_pitre_buoy", "finish"]
    assert route.finished
