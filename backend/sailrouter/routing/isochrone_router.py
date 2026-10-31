from __future__ import annotations

from datetime import datetime

import numpy as np

from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.great_circle import GreatCircle
from sailrouter.geography.obstacle_checker import ObstacleChecker
from sailrouter.polar.maneuver_penalty import ManeuverPenalty
from sailrouter.polar.speed_model import SpeedModel
from sailrouter.routing.heading_fan import HeadingFan
from sailrouter.routing.isochrone import Isochrone
from sailrouter.routing.isochrone_pruner import IsochronePruner
from sailrouter.routing.mark_progress import MarkProgress
from sailrouter.routing.time_schedule import TimeSchedule
from sailrouter.weather.wind_field import WindField


class RoutingError(RuntimeError):
    """The router cannot go on (start on land, every heading blocked...)."""


class IsochroneRouter:
    """Runs the isochrone method for ONE wind field.

    Each step, vectorised over front points × headings: wind at the parent (start of the step) → best sail
    and speed → maneuver penalty against the parent's TWA and sail → destination → mark progress (finishing
    segments stop on the finish line) → prune, dropping segments that cross land or a forbidden zone (only
    those that could survive pruning are checked). Stops at the
    horizon or when a point finishes.
    """

    def __init__(
        self,
        wind: WindField,
        speed_model: SpeedModel,
        penalty: ManeuverPenalty,
        obstacles: ObstacleChecker,
        fan: HeadingFan,
        pruner: IsochronePruner,
    ) -> None:
        self._wind = wind
        self._speed = speed_model
        self._penalty = penalty
        self._obstacles = obstacles
        self._fan = fan
        self._pruner = pruner

    def run(self, start: GeoPoint, schedule: TimeSchedule, progress: MarkProgress) -> list[Isochrone]:
        if self._obstacles.blocked([start.lat_deg], [start.lon_deg], [start.lat_deg], [start.lon_deg])[0]:
            raise RoutingError(f"start position {start} is on land, in a forbidden zone or outside the area")
        times = schedule.times()
        fronts = [Isochrone.origin(times[0], start.lat_deg, start.lon_deg)]
        for begin, end in zip(times, times[1:]):
            front = self._step(fronts[-1], begin, end, progress)
            if len(front) == 0:
                raise RoutingError(f"no reachable position at {end.isoformat()}: every heading is blocked")
            fronts.append(front)
            if front.leg.max() >= progress.finished_leg:
                break
        return fronts

    def _step(self, front: Isochrone, begin: datetime, end: datetime, progress: MarkProgress) -> Isochrone:
        step_s = (end - begin).total_seconds()
        tws, twd = self._wind.wind_at(front.lat_deg, front.lon_deg, begin.timestamp())
        headings = self._fan.headings(progress.bearing_to_target_deg(front.leg, front.lat_deg, front.lon_deg))
        twa = (twd[:, None] - headings + 180.0) % 360.0 - 180.0
        tws_grid = np.broadcast_to(tws[:, None], twa.shape)
        sail, speed = self._speed.best(tws_grid, twa)
        lost_s = self._penalty.loss_s(front.twa_deg[:, None], front.sail[:, None], twa, sail, tws_grid)
        distance_nm = speed * np.maximum(step_s - lost_s, 0.0) / 3600.0
        parent = np.broadcast_to(np.arange(len(front))[:, None], twa.shape).ravel()
        lat0, lon0 = front.lat_deg[parent], front.lon_deg[parent]
        heading = headings.ravel()
        lat1, lon1 = GreatCircle.destination(lat0, lon0, heading, distance_nm.ravel())
        leg = progress.advance(front.leg[parent], lat0, lon0, lat1, lon1)
        lat1, lon1 = progress.end_at_finish(front.leg[parent], leg, lat0, lon0, lat1, lon1)
        moving = np.nonzero(distance_nm.ravel() > 0)[0]
        lat0, lon0, lat1, lon1, parent = lat0[moving], lon0[moving], lat1[moving], lon1[moving], parent[moving]
        candidates = Isochrone(
            time=end,
            lat_deg=lat1,
            lon_deg=lon1,
            parent=parent,
            heading_deg=heading[moving],
            twa_deg=twa.ravel()[moving],
            tws_kn=tws_grid.ravel()[moving],
            sail=sail.ravel()[moving],
            speed_kn=speed.ravel()[moving],
            leg=leg[moving],
        )

        def blocked(indices):
            return self._obstacles.blocked(lat0[indices], lon0[indices], lat1[indices], lon1[indices])

        return self._pruner.prune(candidates, progress, blocked)
