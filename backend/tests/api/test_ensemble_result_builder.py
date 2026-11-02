from datetime import UTC, datetime

from fastapi.testclient import TestClient

from sailrouter.api.app_factory import create_app
from sailrouter.api.ensemble_result_builder import EnsembleResultBuilder
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.ensemble.ensemble_synthesizer import EnsembleSynthesizer
from sailrouter.service.ensemble_report import EnsembleReport
from sailrouter.service.ensemble_status import EnsembleStatus
from sailrouter.service.route_report import RouteReport
from sailrouter.weather.model_run import ModelRun
from tests.ensemble.conftest import course, straight_route

GEFS_RUN = ModelRun("gefs", datetime(2026, 10, 31, 6, tzinfo=UTC))
GFS_RUN = ModelRun("gfs", datetime(2026, 10, 31, 6, tzinfo=UTC))
READY = EnsembleStatus("ready", GEFS_RUN, 1426, 1426, 31)


def ensemble_report() -> EnsembleReport:
    members = {f"p{k:02d}": straight_route(h) for k, h in enumerate([200, 201, 202, 203, 250, 251], start=1)}
    game_route = straight_route(201)
    game = RouteReport("route-du-rhum-2026", "Route du Rhum", "class40", GeoPoint(46.0, -8.0), game_route.start,
                       GFS_RUN, datetime(2026, 10, 31, 17, tzinfo=UTC), course(), game_route, 37)
    synthesis = EnsembleSynthesizer().synthesize(members, game_route, course())
    return EnsembleReport(game, GEFS_RUN, members, synthesis)


def test_ensemble_result_has_options_with_probabilities_members_and_the_game_route():
    result = EnsembleResultBuilder().build(ensemble_report(), READY)
    assert result["weather"]["model"] == "GEFS 0.5°" and result["weather"]["member_count"] == 6
    assert result["weather"]["run"] == "2026-10-31T06:00:00Z" and result["weather"]["game_run"] == "2026-10-31T06:00:00Z"
    assert result["ensemble"] == {"state": "ready", "run": "2026-10-31T06:00:00Z", "done": 1426, "total": 1426,
                                  "member_count": 31}
    first, second = result["options"]
    assert result["recommended_option"] == first["id"] and result["advice"]["key"] == "advice.head_direction"
    assert (first["member_count"], first["probability"], second["probability"]) == (4, 0.667, 0.333)
    assert first["game_route"] and not second["game_route"]
    assert first["kind"] in ("shortest", "positioning") and first["eta_delta_h"] >= 0
    assert [s["hour"] for s in first["steps"]] == [4, 8, 12, 16, 24, 48]
    assert first["steps"][0]["confidence"] == 1.0 and first["steps"][0]["zone_radius_nm"] == 7
    assert len(first["path"]) == 61 and first["legs"] and first["now"]["sail"] == "Spi"
    assert len(result["members"]) == 6
    member = result["members"][4]
    assert member["member"] == "p05" and member["option"] == second["id"] and len(member["path"]) == 61
    assert all(len(str(value).split(".")[-1]) <= 3 for value in member["path"][7])
    assert result["ideal_route"]["to_go_nm"] == 2500 and not result["ideal_route"]["finished"]
    assert result["next_mark"] == {"id": course().legs[0].mark_id, "auto": True}


def test_without_a_current_route_the_options_are_compared_with_the_recommended_one():
    result = EnsembleResultBuilder().build(ensemble_report(), READY)
    assert result["outlook_reference"] == "recommended" and result["current_route"] is None


def test_with_a_current_route_the_options_are_compared_with_it():
    report = ensemble_report()
    per_option = [{"p01": {48.0: 100.0}}, {"p01": {48.0: 120.0}}]
    report = EnsembleReport(report.game, report.gefs_run, report.member_routes, report.synthesis, {}, per_option,
                            {"p01": {48.0: 110.0}})
    result = EnsembleResultBuilder().build(report, READY)
    assert result["outlook_reference"] == "current_route"
    assert result["current_route"] == {"outlook": [{"hours": 48, "to_go_nm": 110, "gain_nm": 0.0, "worst_nm": 0.0,
                                                    "ahead_share": 0.0}]}
    assert [o["outlook"][0]["gain_nm"] for o in result["options"]] == [10.0, -10.0]


class FakeJob:
    def status(self):
        return EnsembleStatus("downloading", GEFS_RUN, 400, 1426, 31)


def test_status_endpoint_reports_the_download_progress():
    client = TestClient(create_app(ensemble_job=FakeJob(), refresh_in_background=False))
    assert client.get("/api/ensemble/status").json() == {
        "state": "downloading", "run": "2026-10-31T06:00:00Z", "done": 400, "total": 1426, "member_count": 31}
