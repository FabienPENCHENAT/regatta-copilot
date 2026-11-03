from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from sailrouter.api.app_factory import create_app
from sailrouter.api.route_result_builder import RouteResultBuilder
from sailrouter.api.schemas import BoatOptionsIn
from sailrouter.routing.route import Route
from sailrouter.routing.route_point import RoutePoint
from sailrouter.service.ensemble_status import EnsembleStatus


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(refresh_in_background=False))


def test_lists_races_with_their_boats(client):
    races = client.get("/api/races").json()
    rhum = next(r for r in races if r["id"] == "route-du-rhum-2026")
    assert rhum["default_boat"] == "class40" and "imoca" in rhum["boats"]


def test_serves_the_boat_polar_for_manoeuvre_times(client):
    winch = client.get("/api/races/route-du-rhum-2026/boats/class40/polar").json()["winch"]
    assert winch["tack"]["std"]["lw"] == {"ratio": 0.5, "timer": 180}


def test_unknown_race_and_unknown_boat_are_refused(client):
    assert client.get("/api/races/nope").status_code == 404
    assert client.get("/api/races/route-du-rhum-2026/boats/submarine/polar").status_code == 404
    bad = client.post("/api/route", json={"race_id": "nope", "position": {"lat": 48.7, "lon": -1.9}})
    assert bad.status_code in (400, 404)


def test_settings_become_boat_options_with_everything_off_by_default():
    options = BoatOptionsIn(sails=["Code0", "Magic"]).to_options()
    assert options.allows_sail("Code0") and not options.allows_sail("LightGnk")
    assert not (options.foil or options.hull or options.pro_winch)
    assert BoatOptionsIn(foil=True, pro_winch=True).to_options().pro_winch


def test_result_has_an_hourly_path_and_the_plan_hours_the_route_covers():
    start = datetime(2026, 11, 1, 12, tzinfo=UTC)
    points = tuple(
        RoutePoint(start + timedelta(hours=h), 48.7 - 0.1 * h, -2.0 - 0.2 * h, 0, 250, 140, 12.0, "Spi", 10.0)
        for h in (0, 1, 2, 3, 4, 7, 10)
    )
    report = type("Report", (), {})()
    report.__dict__.update(race_id="r", boat_id="b", position=type("P", (), {"lat_deg": 48.7, "lon_deg": -2.0})(),
                           weather_run=type("Run", (), {"cycle": start})(), next_run_expected=start,
                           route=Route(points, distance_to_go_nm=3000.0, finished=False),
                           next_mark_id="tete_anglais", next_mark_auto=True)
    result = RouteResultBuilder().build(report, EnsembleStatus("downloading", None, 12, 1426, 31))
    assert result["ensemble"] == {"state": "downloading", "run": None, "done": 12, "total": 1426, "member_count": 31}
    assert result["weather"]["member_count"] == 1 and result["members"] == []
    assert result["next_mark"] == {"id": "tete_anglais", "auto": True}
    option = result["options"][0]
    assert len(option["path"]) == 11  # one point per hour, 0 to 10 h
    assert option["path"][5] == [round(48.7 - 0.1 * 5, 4), round(-2.0 - 0.2 * 5, 4)]  # interpolated between 4 h and 7 h
    assert [s["hour"] for s in option["steps"]] == [4, 8]
    assert len(option["hourly"]) == 11 and option["hourly"][10] == option["hourly"][9]  # end point: last leg's
    assert option["hourly"][5] == {"heading_deg": 250, "twa_deg": 140, "tws_kn": 12.0, "sail": "Spi", "speed_kn": 10.0}
    assert option["probability"] is None and option["steps"][0]["confidence"] is None
    assert [(leg["start_hour"], leg["end_hour"]) for leg in option["legs"]] == [(0, 10)]


@pytest.mark.parametrize("boat", ["class40", "imoca", "ocean_fifty", "ultim", "vintage_multi"])
def test_every_rhum_boat_has_a_polar(client, boat):
    polar = client.get(f"/api/races/route-du-rhum-2026/boats/{boat}/polar").json()
    assert len(polar["sail"]) == 7 and "winch" in polar


def test_wind_hours_must_be_whole_numbers_in_the_route_window(client):
    assert client.get("/api/wind", params={"start": "2026-11-01T12:00:00Z", "hours": "abc"}).status_code == 400
    assert client.get("/api/wind", params={"start": "2026-11-01T12:00:00Z", "hours": "500"}).status_code == 400


def test_polar_curves_follow_the_options(client):
    url = "/api/races/route-du-rhum-2026/boats/class40/polar/curves"
    bare = client.get(url, params={"tws": "12"}).json()
    full = client.get(url, params={"tws": "12", "sails": "Code0,LightJib", "foil": "true", "hull": "true"}).json()
    at_90 = bare["twa"].index(90.0)
    assert bare["curves"][0]["sail"][at_90] in ("Jib", "Spi")
    assert full["curves"][0]["sail"][at_90] == "Code0"
    assert full["curves"][0]["speed"][at_90] > bare["curves"][0]["speed"][at_90]
    assert client.get(url, params={"tws": "abc"}).status_code == 400


def test_latest_weather_gives_the_game_run_and_the_scenarios_state(client):
    latest = client.get("/api/weather/latest").json()
    assert set(latest) == {"game_run", "ensemble"}
    assert latest["game_run"] is None or latest["game_run"].endswith("Z")
    assert latest["ensemble"]["state"] in {"ready", "downloading", "unavailable"}
