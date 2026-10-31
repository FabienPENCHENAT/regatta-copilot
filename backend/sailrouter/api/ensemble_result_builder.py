from __future__ import annotations

from sailrouter.api.ensemble_status_json import ensemble_status_json
from sailrouter.api.route_json_writer import RouteJsonWriter, iso
from sailrouter.ensemble.route_option import RouteOption
from sailrouter.service.ensemble_report import EnsembleReport
from sailrouter.service.ensemble_status import EnsembleStatus

MEMBER_PATH_DECIMALS = 3


class EnsembleResultBuilder:
    """`EnsembleReport` → the route result JSON with route options and probabilities
    (docs/ai/api-contract.md). `ideal_route` stays the game's route (deterministic GFS)."""

    def __init__(self) -> None:
        self._writer = RouteJsonWriter()

    def build(self, report: EnsembleReport, ensemble: EnsembleStatus) -> dict:
        game, synthesis = report.game, report.synthesis
        return {
            "race_id": game.race_id,
            "boat_id": game.boat_id,
            "position": {"lat": game.position.lat_deg, "lon": game.position.lon_deg},
            "computed_at": iso(game.route.start),
            "weather": {
                "model": "GEFS 0.5°",
                "run": iso(report.gefs_run.cycle),
                "game_model": "GFS 0.25°",
                "game_run": iso(game.weather_run.cycle),
                "next_run_expected": iso(game.next_run_expected),
                "member_count": synthesis.member_total,
            },
            "ensemble": ensemble_status_json(ensemble),
            "next_mark": {"id": game.next_mark_id, "auto": game.next_mark_auto},
            "recommended_option": synthesis.recommended.id,
            "advice": synthesis.advice,
            "options": [self._option(option) for option in synthesis.options],
            "members": [
                {"member": member, "option": synthesis.member_options[member],
                 "path": self._writer.hourly_path(route, MEMBER_PATH_DECIMALS),
                 # drawn: every route point, so the thin lines go round zones like the routes really do
                 "line": [[round(p.lat_deg, 4), round(p.lon_deg, 4)] for p in route.points]}
                for member, route in report.member_routes.items()
            ],
            "ideal_route": self._writer.track(game.route),
        }

    def _option(self, option: RouteOption) -> dict:
        return {
            "id": option.id,
            "kind": option.kind,
            "member_count": len(option.members),
            "probability": round(option.probability, 3),
            "game_route": option.game_route,
            "eta_delta_h": round(option.eta_delta_h, 1),
            "representative_member": option.representative,
            "dtf_end_nm": round(option.route.distance_to_go_nm),
            **self._writer.option_body(option.route, option.confidence_by_hour),
        }
