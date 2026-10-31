from __future__ import annotations

from datetime import UTC, datetime

import numpy as np

from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.polar.boat_options import BoatOptions
from sailrouter.polar.winch_timings import ManeuverTiming
from sailrouter.service.project_paths import ProjectPaths
from sailrouter.service.route_planner import RoutePlanner
from sailrouter.service.route_report import RouteReport

HORIZON_H = 120.0
CHECKPOINTS_H = (24, 48, 120)


class OptionsImpact:
    """What a change of boat options is worth on the real weather: the game's route (GFS) with the current
    options and with the changed ones, from the same position; the gain is the difference in distance to go
    (through the next marks) at +24 h, +48 h and +120 h. Positive = the changed options are faster."""

    def __init__(self, paths: ProjectPaths) -> None:
        self._paths = paths

    def compare(self, race_id: str, boat_id: str | None, position: GeoPoint, current: BoatOptions,
                changed: BoatOptions, maneuvers: dict[str, ManeuverTiming], next_mark: str | None) -> dict:
        race = RaceCatalog(self._paths.races_dir).load(race_id)
        start = max(race.start_time, datetime.now(UTC))
        reports = [
            RoutePlanner(self._paths, prefer_cached=True).plan(
                race_id, boat_id, position, HORIZON_H, start, next_mark, options, maneuvers)
            for options in (current, changed)
        ]
        gains = []
        for hours in CHECKPOINTS_H:
            before, after = (self._distance_to_go(report, hours) for report in reports)
            gains.append({"hours": hours, "gain_nm": round(before - after, 1)})
        return {"start": start.isoformat().replace("+00:00", "Z"), "gains": gains,
                "run": reports[0].weather_run.cycle.isoformat().replace("+00:00", "Z")}

    @staticmethod
    def _distance_to_go(report: RouteReport, hours: float) -> float:
        route = report.route
        hours = min(hours, route.duration_h)
        lat, lon = route.position_at(hours)
        leg = route.point_at(hours).marks_passed
        return float(report.progress.distance_to_go_nm(np.array([leg]), np.array([lat]), np.array([lon]))[0])
