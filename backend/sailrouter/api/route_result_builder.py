from __future__ import annotations

from datetime import timedelta

from sailrouter.domain.great_circle import GreatCircle
from sailrouter.routing.route import Route
from sailrouter.routing.route_leg_splitter import RouteLeg, RouteLegSplitter
from sailrouter.routing.route_point import RoutePoint
from sailrouter.service.route_report import RouteReport

PLAN_HOURS = (4, 8, 12, 16, 24, 48)
GAME_OPTION_ID = "gfs"


class RouteResultBuilder:
    """`RouteReport` → the JSON the frontend reads (docs/ai/api-contract.md).

    Until the ensemble exists (step 4) there is one option, the route on the game's weather: no scenario
    members, no probability and no confidence (null values the frontend shows as "not available yet").
    """

    def build(self, report: RouteReport) -> dict:
        route = report.route
        return {
            "race_id": report.race_id,
            "boat_id": report.boat_id,
            "position": {"lat": report.position.lat_deg, "lon": report.position.lon_deg},
            "computed_at": _iso(route.start),
            "weather": {
                "model": "GFS 0.25°",
                "run": _iso(report.weather_run.cycle),
                "next_run_expected": _iso(report.next_run_expected),
                "member_count": 1,
            },
            "recommended_option": GAME_OPTION_ID,
            "advice": {"key": "advice.follow_game_route", "params": {"hours": 48}},
            "options": [self._game_option(route)],
            "members": [],
            "ideal_route": self._track(route),
        }

    def _game_option(self, route: Route) -> dict:
        return {
            "id": GAME_OPTION_ID,
            "kind": "game",
            "member_count": 1,
            "probability": None,
            "game_route": True,
            "eta_delta_h": 0.0,
            "now": _settings(route.points[0]),
            "steps": [self._step(route, hour) for hour in PLAN_HOURS if route.covers(hour)],
            "path": _hourly_path(route),
            "legs": [self._leg(route, leg) for leg in RouteLegSplitter().split(route)],
        }

    @staticmethod
    def _leg(route: Route, leg: RouteLeg) -> dict:
        hours = lambda moment: round((moment - route.start) / timedelta(hours=1), 2)  # noqa: E731
        return {
            "start_hour": hours(leg.start), "end_hour": hours(leg.end),
            "heading_deg": round(leg.heading_deg), "sail": leg.sail, "twa_deg": round(leg.twa_deg),
            "tws_min_kn": round(leg.tws_min_kn, 1), "tws_max_kn": round(leg.tws_max_kn, 1),
            "speed_kn": round(leg.speed_kn, 1),
            "lat": round(leg.start_point.lat_deg, 4), "lon": round(leg.start_point.lon_deg, 4),
            "end_lat": round(leg.end_point.lat_deg, 4), "end_lon": round(leg.end_point.lon_deg, 4),
        }

    @staticmethod
    def _step(route: Route, hour: int) -> dict:
        point = route.point_at(hour)
        return {
            "hour": hour,
            "lat": round(point.lat_deg, 4),
            "lon": round(point.lon_deg, 4),
            **_settings(point),
            "confidence": None,
            "zone_radius_nm": round(3 + hour * 0.9),
        }

    @staticmethod
    def _track(route: Route) -> dict:
        lat = [p.lat_deg for p in route.points]
        lon = [p.lon_deg for p in route.points]
        sailed = float(GreatCircle.distance_nm(lat[:-1], lon[:-1], lat[1:], lon[1:]).sum())
        return {
            "path": [[round(a, 4), round(b, 4)] for a, b in zip(lat, lon)],
            "distance_nm": round(sailed),
            "to_go_nm": round(route.distance_to_go_nm),
            "finished": route.finished,
        }


def _settings(point: RoutePoint) -> dict:
    return {
        "heading_deg": round(point.heading_deg or 0),
        "twa_deg": round(point.twa_deg or 0),
        "tws_kn": round(point.tws_kn or 0, 1),
        "sail": point.sail,
        "speed_kn": round(point.speed_kn or 0, 1),
    }


def _hourly_path(route: Route) -> list[list[float]]:
    """One position per hour from the start (the map places the boat at path[hour]), interpolated
    between route points, which are hourly for 24 h and 3-hourly after."""
    path, points = [], route.points
    hours = int((route.end - route.start) / timedelta(hours=1))
    for hour in range(hours + 1):
        moment = route.start + timedelta(hours=hour)
        after = next(i for i, p in enumerate(points) if p.time >= moment)
        before = max(after - 1, 0)
        span = (points[after].time - points[before].time).total_seconds() or 1.0
        w = (moment - points[before].time).total_seconds() / span if after != before else 0.0
        lat = points[before].lat_deg + w * (points[after].lat_deg - points[before].lat_deg)
        lon = points[before].lon_deg + w * (points[after].lon_deg - points[before].lon_deg)
        path.append([round(lat, 4), round(lon, 4)])
    return path


def _iso(moment) -> str:
    return moment.isoformat().replace("+00:00", "Z")
