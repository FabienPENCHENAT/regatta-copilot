from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sailrouter.cli.route_report import RouteReport
from sailrouter.cli.route_summary_printer import HORIZONS_H
from sailrouter.routing.route_point import RoutePoint


class RouteFileWriter:
    """Writes a `RouteReport` as `<name>.json` (route plan + every point) and `<name>.geojson`
    (a LineString of the route plus one Point per horizon, for the map)."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def write(self, report: RouteReport, name: str) -> tuple[Path, Path]:
        self._directory.mkdir(parents=True, exist_ok=True)
        json_path = self._directory / f"{name}.json"
        geojson_path = self._directory / f"{name}.geojson"
        json_path.write_text(json.dumps(self._document(report), indent=1), encoding="utf-8")
        geojson_path.write_text(json.dumps(self._geojson(report)), encoding="utf-8")
        return json_path, geojson_path

    def _document(self, report: RouteReport) -> dict[str, Any]:
        route = report.route
        return {
            "race_id": report.race_id,
            "boat_id": report.boat_id,
            "position": {"lat": round(report.position.lat_deg, 5), "lon": round(report.position.lon_deg, 5)},
            "computed_at": _iso(report.computed_at),
            "start": _iso(route.start),
            "weather": {"model": "GFS 0.25°", "run": _iso(report.weather_run.cycle),
                        "next_run_expected": _iso(report.next_run_expected), "member_count": 1},
            "finished": route.finished,
            "distance_to_go_nm": round(route.distance_to_go_nm, 1),
            "steps": [self._point(route.point_at(h), report) for h in HORIZONS_H if route.covers(h)],
            "points": [self._point(point, report) for point in route.points],
            "path": [[round(p.lat_deg, 5), round(p.lon_deg, 5)] for p in route.points],
            "compute_s": {name: round(seconds, 2) for name, seconds in report.timings_s.items()},
        }

    @staticmethod
    def _point(point: RoutePoint, report: RouteReport) -> dict[str, Any]:
        hours = (point.time - report.route.start).total_seconds() / 3600
        return {
            "hour": round(hours, 2),
            "time": _iso(point.time),
            "lat": round(point.lat_deg, 5),
            "lon": round(point.lon_deg, 5),
            "heading_deg": _round(point.heading_deg, 0),
            "twa_deg": _round(point.twa_deg, 0),
            "tws_kn": _round(point.tws_kn, 1),
            "sail": point.sail,
            "speed_kn": _round(point.speed_kn, 2),
            "marks_passed": point.marks_passed,
        }

    def _geojson(self, report: RouteReport) -> dict[str, Any]:
        route = report.route
        line = {
            "type": "Feature",
            "properties": {"race_id": report.race_id, "boat_id": report.boat_id,
                           "run": _iso(report.weather_run.cycle), "start": _iso(route.start)},
            "geometry": {"type": "LineString",
                         "coordinates": [[round(p.lon_deg, 5), round(p.lat_deg, 5)] for p in route.points]},
        }
        marks = [
            {"type": "Feature", "properties": self._point(route.point_at(h), report),
             "geometry": {"type": "Point", "coordinates": [round(route.point_at(h).lon_deg, 5),
                                                           round(route.point_at(h).lat_deg, 5)]}}
            for h in HORIZONS_H if route.covers(h)
        ]
        return {"type": "FeatureCollection", "features": [line, *marks]}


def _iso(moment) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _round(value: float | None, digits: int) -> float | None:
    return None if value is None else round(value, digits)
