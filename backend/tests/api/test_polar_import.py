import json

import pytest
from fastapi.testclient import TestClient

from sailrouter.api.app_factory import create_app
from sailrouter.service.project_paths import REPO_ROOT, ProjectPaths

POLAR_URL = "/api/races/route-du-rhum-2026/boats/class40/polar"


@pytest.fixture
def project(tmp_path) -> ProjectPaths:
    """A project root sharing the real races, polars and frontend, with its own runtime folder (var/)."""
    for name in ("races", "data", "frontend"):
        (tmp_path / name).symlink_to(REPO_ROOT / name)
    return ProjectPaths(tmp_path)


@pytest.fixture
def client(project) -> TestClient:
    return TestClient(create_app(project, refresh_in_background=False))


@pytest.fixture
def game_polar() -> dict:
    polar = json.loads((REPO_ROOT / "data/polars/class40-2021.vr.json").read_text(encoding="utf-8"))
    polar["label"] = "mono/class40-2021-player"
    return polar


def test_community_polar_by_default(client):
    polar = client.get(POLAR_URL).json()
    assert polar["_source"] == "community" and polar["_imported_at"] is None
    assert polar["winch"]["tack"]["std"]["lw"] == {"ratio": 0.5, "timer": 180}


def test_import_from_a_game_response_then_remove(client, project, game_polar):
    wrapped = {"@class": "LogEventResponse", "authToken": "do-not-keep", "scriptData": {"polar": game_polar}}
    imported = client.post(POLAR_URL, json=wrapped)
    assert imported.status_code == 200
    assert imported.json()["_source"] == "player" and imported.json()["_imported_at"].endswith("Z")
    stored = project.polars_dir / "route-du-rhum-2026-class40.vr.json"
    assert json.loads(stored.read_text()) == game_polar  # the wrapper (and its token) is not kept
    assert client.get(POLAR_URL).json()["label"] == "mono/class40-2021-player"
    removed = client.delete(POLAR_URL).json()
    assert removed["_source"] == "community" and not stored.exists()


def test_invalid_polar_is_refused_with_a_clear_message(client, game_polar):
    game_polar["sail"] = game_polar["sail"][:5]
    response = client.post(POLAR_URL, json={"res": game_polar})
    assert response.status_code == 400 and "7 sails" in response.json()["detail"]
    assert client.post(POLAR_URL, json={"nothing": "here"}).status_code == 400


def test_unknown_race_or_boat_is_404(client, game_polar):
    assert client.get("/api/races/route-du-rhum-2026/boats/submarine/polar").status_code == 404
    assert client.post("/api/races/nope/boats/class40/polar", json=game_polar).status_code == 404


def test_unknown_next_mark_is_refused_before_any_computation(client):
    response = client.post("/api/route", json={"race_id": "route-du-rhum-2026", "boat_id": "class40",
                                               "position": {"lat": 17.0, "lon": -60.0}, "next_mark": "nowhere"})
    assert response.status_code == 400 and "tete_anglais" in response.json()["detail"]
