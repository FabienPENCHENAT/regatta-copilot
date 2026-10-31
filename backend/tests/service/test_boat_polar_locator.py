import json
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.great_circle import GreatCircle
from sailrouter.service.boat_polar_locator import BoatPolarLocator
from sailrouter.service.player_polar_store import PlayerPolarStore
from sailrouter.service.project_paths import REPO_ROOT, ProjectPaths
from sailrouter.service.route_planner import RoutePlanner
from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.wind_field import WindField
from sailrouter.weather.wind_grid import WindGrid

RACE = "route-du-rhum-2026"
START = datetime(2026, 11, 3, 12, tzinfo=UTC)


@pytest.fixture
def project(tmp_path) -> ProjectPaths:
    for name in ("races", "data", "frontend"):
        (tmp_path / name).symlink_to(REPO_ROOT / name)
    return ProjectPaths(tmp_path)


def slow_copy_of_class40() -> dict:
    """The community Class40 polar at half speed: an imported polar that is easy to recognise in a route."""
    polar = json.loads((REPO_ROOT / "data/polars/class40-2021.vr.json").read_text(encoding="utf-8"))
    for sail in polar["sail"]:
        sail["speed"] = [[speed / 2 for speed in row] for row in sail["speed"]]
    return polar


def test_player_polar_replaces_the_community_one_until_removed(project):
    boat = RaceCatalog(project.races_dir).load(RACE).boat("class40")
    locator, store = BoatPolarLocator(project), PlayerPolarStore(project.polars_dir)
    assert locator.polar_file(RACE, boat) == project.root / "data/polars/class40-2021.vr.json"
    assert (locator.source(RACE, boat), locator.fingerprint(RACE, boat)) == ("community", "community")
    store.save(RACE, "class40", slow_copy_of_class40())
    assert locator.polar_file(RACE, boat) == project.polars_dir / "route-du-rhum-2026-class40.vr.json"
    assert locator.source(RACE, boat) == "player" and locator.fingerprint(RACE, boat).startswith("player@")
    store.delete(RACE, "class40")
    assert locator.source(RACE, boat) == "community"


def test_store_refuses_ids_that_could_escape_its_folder(project):
    with pytest.raises(ValueError):
        PlayerPolarStore(project.polars_dir).path("../races", "class40")


def test_planner_sails_with_the_imported_polar(project, monkeypatch):
    lat, lon = np.arange(40.0, 50.25, 0.25), np.arange(-20.0, -4.75, 0.25)
    u = np.full((lat.size, lon.size), 7.0, np.float32)  # wind from the west, ≈ 14 kn
    wind = WindField([WindGrid(START + timedelta(hours=h), lat, lon, u, np.zeros_like(u)) for h in (0, 24)])
    run = ModelRun("gfs", START - timedelta(hours=6))
    monkeypatch.setattr(RoutePlanner, "_wind_field", lambda self, schedule, now: (wind, run))

    def sailed_nm() -> float:
        points = RoutePlanner(project).plan(RACE, "class40", GeoPoint(45.0, -12.0), 6, START).route.points
        return float(sum(GreatCircle.distance_nm(a.lat_deg, a.lon_deg, b.lat_deg, b.lon_deg)
                         for a, b in zip(points, points[1:])))

    community = sailed_nm()
    PlayerPolarStore(project.polars_dir).save(RACE, "class40", slow_copy_of_class40())
    player = sailed_nm()
    assert player == pytest.approx(community / 2, rel=0.15)

