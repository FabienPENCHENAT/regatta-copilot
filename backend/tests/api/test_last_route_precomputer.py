from datetime import UTC, datetime, timedelta

from sailrouter.api.cached_route_computer import _cache_inputs
from sailrouter.api.last_route_precomputer import LastRoutePrecomputer
from sailrouter.api.last_route_request_store import LastRouteRequestStore
from sailrouter.api.route_result_cache import RouteResultCache
from sailrouter.api.schemas import RouteRequest
from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.service.project_paths import REPO_ROOT
from sailrouter.weather.model_run import ModelRun

NOW = datetime(2026, 11, 2, 17, tzinfo=UTC)
REQUEST = RouteRequest(race_id="route-du-rhum-2026", boat_id="class40", position={"lat": 45.0, "lon": -12.0},
                       next_mark="tete_anglais")


class FakeComputer:
    def __init__(self):
        self.requests = []

    def result(self, request, from_player=True):
        self.requests.append(request)
        return {}

    def window(self, race, now):
        return max(race.start_time, now), max(race.start_time, now) + timedelta(hours=120)


def precomputer(tmp_path, received_at=NOW):
    store = LastRouteRequestStore(tmp_path / "last_request.json")
    computer = FakeComputer()
    if received_at:
        store.save(REQUEST, received_at)
    return LastRoutePrecomputer(store, computer, RaceCatalog(REPO_ROOT / "races"), now=lambda: NOW), computer


def test_last_request_survives_a_restart(tmp_path):
    LastRouteRequestStore(tmp_path / "last.json").save(REQUEST, NOW)
    request, received_at = LastRouteRequestStore(tmp_path / "last.json").load()
    assert request == REQUEST and received_at == NOW


def test_unreadable_file_is_ignored(tmp_path):
    (tmp_path / "last.json").write_text("{broken")
    assert LastRouteRequestStore(tmp_path / "last.json").load() is None


def test_new_weather_recomputes_the_last_request_even_an_old_one(tmp_path):
    run, computer = precomputer(tmp_path, received_at=NOW - timedelta(days=1))
    assert run.precompute(weather_changed=True) and computer.requests == [REQUEST]
    assert not run.precompute(weather_changed=False)  # too old to keep warm
    assert computer.requests == [REQUEST]


def test_recent_request_is_kept_warm_between_runs(tmp_path):
    run, computer = precomputer(tmp_path, received_at=NOW - timedelta(hours=1))
    assert run.precompute(weather_changed=False) and len(computer.requests) == 1


def test_nothing_to_precompute_before_the_first_request_but_a_window_anyway(tmp_path):
    run, computer = precomputer(tmp_path, received_at=None)
    assert not run.precompute(weather_changed=True) and computer.requests == []
    start, end = run.window(NOW)
    assert start == NOW and end - start == timedelta(hours=120)


def test_cache_key_changes_with_the_next_mark_and_the_polar():
    start, gfs = NOW, ModelRun("gfs", NOW - timedelta(hours=11))
    base = RouteResultCache.key(_cache_inputs(REQUEST, start, gfs, None, "community"))
    auto = REQUEST.model_copy(update={"next_mark": None})
    assert RouteResultCache.key(_cache_inputs(auto, start, gfs, None, "community")) != base
    assert RouteResultCache.key(_cache_inputs(REQUEST, start, gfs, None, "player@1.0")) != base
