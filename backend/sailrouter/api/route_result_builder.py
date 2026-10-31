from __future__ import annotations

from sailrouter.api.ensemble_status_json import ensemble_status_json
from sailrouter.api.route_json_writer import RouteJsonWriter, iso
from sailrouter.service.ensemble_status import EnsembleStatus
from sailrouter.service.route_report import RouteReport

GAME_OPTION_ID = "gfs"


class RouteResultBuilder:
    """`RouteReport` → the JSON the frontend reads when the GEFS ensemble is not on disk yet
    (docs/ai/api-contract.md): one option, the route on the game's weather, with no scenario members,
    no probability and no confidence (null values the frontend shows as "not available yet")."""

    def __init__(self) -> None:
        self._writer = RouteJsonWriter()

    def build(self, report: RouteReport, ensemble: EnsembleStatus) -> dict:
        route = report.route
        return {
            "race_id": report.race_id,
            "boat_id": report.boat_id,
            "position": {"lat": report.position.lat_deg, "lon": report.position.lon_deg},
            "computed_at": iso(route.start),
            "weather": {
                "model": "GFS 0.25°",
                "run": iso(report.weather_run.cycle),
                "next_run_expected": iso(report.next_run_expected),
                "member_count": 1,
            },
            "ensemble": ensemble_status_json(ensemble),
            "next_mark": {"id": report.next_mark_id, "auto": report.next_mark_auto},
            "recommended_option": GAME_OPTION_ID,
            "advice": {"key": "advice.follow_game_route", "params": {"hours": 48}},
            "options": [{
                "id": GAME_OPTION_ID, "kind": "game", "member_count": 1, "probability": None, "game_route": True,
                "eta_delta_h": 0.0, **self._writer.option_body(route),
            }],
            "members": [],
            "ideal_route": self._writer.track(route),
        }
