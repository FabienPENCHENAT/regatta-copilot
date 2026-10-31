from __future__ import annotations

from datetime import datetime, timedelta

from sailrouter.domain.great_circle import GreatCircle
from sailrouter.ensemble.confidence_grader import ConfidenceGrader
from sailrouter.ensemble.ensemble_synthesizer import PLAN_HOURS
from sailrouter.routing.route import Route
from sailrouter.routing.route_leg_splitter import RouteLeg, RouteLegSplitter
from sailrouter.routing.route_point import RoutePoint


class RouteJsonWriter:
    """One `Route` → the JSON pieces of an option (docs/ai/api-contract.md): settings now, plan steps, legs,
    hourly path, full track. Shared by the GFS-only and the ensemble result builders."""

    def option_body(self, route: Route, confidence_by_hour: dict[int, float] | None = None) -> dict:
        """`now`, `steps`, `path`, `legs`; step confidence is null when not given."""
        confidence_by_hour = confidence_by_hour or {}
        return {
            "now": self.settings(route.points[0]),
            "steps": [self.step(route, hour, confidence_by_hour.get(hour)) for hour in PLAN_HOURS if route.covers(hour)],
            "path": self.hourly_path(route),
            "legs": [self.leg(route, leg) for leg in RouteLegSplitter().split(route)],
        }

    @staticmethod
    def settings(point: RoutePoint) -> dict:
        return {
            "heading_deg": round(point.heading_deg or 0),
            "twa_deg": round(point.twa_deg or 0),
            "tws_kn": round(point.tws_kn or 0, 1),
            "sail": point.sail,
            "speed_kn": round(point.speed_kn or 0, 1),
        }

    def step(self, route: Route, hour: int, confidence: float | None) -> dict:
        point = route.point_at(hour)
        return {
            "hour": hour,
            "lat": round(point.lat_deg, 4),
            "lon": round(point.lon_deg, 4),
            **self.settings(point),
            "confidence": None if confidence is None else round(confidence, 2),
            "zone_radius_nm": ConfidenceGrader.zone_radius_nm(hour),
        }

    @staticmethod
    def leg(route: Route, leg: RouteLeg) -> dict:
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
    def hourly_path(route: Route, decimals: int = 4) -> list[list[float]]:
        """One position per hour from the start (the map places the boat at path[hour])."""
        hours = int(route.duration_h + 1e-6)
        return [[round(value, decimals) for value in route.position_at(hour)] for hour in range(hours + 1)]

    @staticmethod
    def track(route: Route) -> dict:
        lat = [p.lat_deg for p in route.points]
        lon = [p.lon_deg for p in route.points]
        sailed = float(GreatCircle.distance_nm(lat[:-1], lon[:-1], lat[1:], lon[1:]).sum())
        return {
            "path": [[round(a, 4), round(b, 4)] for a, b in zip(lat, lon)],
            "distance_nm": round(sailed),
            "to_go_nm": round(route.distance_to_go_nm),
            "finished": route.finished,
        }


def iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")
