from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sailrouter.routing.route import Route
from sailrouter.routing.route_point import RoutePoint

NM_PER_DEG = 60.0


@dataclass(frozen=True)
class RouteLeg:
    """A stretch of the route sailed with the same orders: one constant heading, one sail, one tack."""

    start: datetime
    end: datetime
    start_point: RoutePoint
    end_point: RoutePoint
    heading_deg: float
    sail: str
    twa_deg: float
    tws_min_kn: float
    tws_max_kn: float
    speed_kn: float


class RouteLegSplitter:
    """Cuts a route into the orders the player types into the game, which then holds a CONSTANT heading (a
    rhumb line). An order is extended point by point while the straight line from its start to the next point
    stays within `max_offset_nm` of every route point in between, with the same sail on the same tack, and
    (when `blocked` is given) does not enter land, a zone or their safety margins; a sail change, a tack or a
    gybe always starts a new order. Its heading is that straight line's: following the plan keeps the boat
    near the computed route and as clear of hazards as the route itself.
    """

    def __init__(self, max_offset_nm: float = 1.5,
                 blocked: Callable[[float, float, float, float], bool] | None = None) -> None:
        self._max_offset_nm = max_offset_nm
        self._blocked = blocked or (lambda lat0, lon0, lat1, lon1: False)

    def split(self, route: Route) -> list[RouteLeg]:
        points = route.points
        legs: list[RouteLeg] = []
        start = 0
        while start < len(points) - 1 and points[start].heading_deg is not None:
            end = start + 1
            while (end < len(points) - 1 and points[end].heading_deg is not None
                   and self._same_orders(points[start], points[end])
                   and self._straight_enough(points[start : end + 2])):
                end += 1
            legs.append(self._leg(points[start:end], points[end]))
            start = end
        return legs

    @staticmethod
    def _same_orders(first: RoutePoint, point: RoutePoint) -> bool:
        return point.sail == first.sail and (point.twa_deg >= 0) == (first.twa_deg >= 0)

    def _straight_enough(self, points: tuple[RoutePoint, ...]) -> bool:
        """Every point within the offset of the rhumb line from the first point to the last."""
        first, last = points[0], points[-1]
        if self._blocked(first.lat_deg, first.lon_deg, last.lat_deg, last.lon_deg):
            return False
        ax, ay = _mercator(first, first)
        bx, by = _mercator(last, first)
        dx, dy = bx - ax, by - ay
        length2 = dx * dx + dy * dy
        for point in points[1:-1]:
            px, py = _mercator(point, first)
            t = 0.0 if length2 == 0 else min(max(((px - ax) * dx + (py - ay) * dy) / length2, 0.0), 1.0)
            if math.hypot(px - (ax + t * dx), py - (ay + t * dy)) > self._max_offset_nm:
                return False
        return True

    @staticmethod
    def _leg(points: tuple[RoutePoint, ...], end: RoutePoint) -> RouteLeg:
        first = points[0]
        heading = _rhumb_bearing_deg(first, end)
        turned = (heading - first.heading_deg + 180.0) % 360.0 - 180.0
        winds = [p.tws_kn for p in points]
        return RouteLeg(
            start=first.time, end=end.time, start_point=first, end_point=end,
            heading_deg=heading, sail=first.sail, twa_deg=first.twa_deg - turned,
            tws_min_kn=min(winds), tws_max_kn=max(winds),
            speed_kn=sum(p.speed_kn for p in points) / len(points),
        )


def _mercator(point: RoutePoint, origin: RoutePoint) -> tuple[float, float]:
    """Mercator coordinates in nm at the origin's latitude: rhumb lines are straight, nearby distances true."""
    scale = math.cos(math.radians(origin.lat_deg)) * NM_PER_DEG
    y = math.degrees(math.log(math.tan(math.pi / 4 + math.radians(point.lat_deg) / 2)))
    y0 = math.degrees(math.log(math.tan(math.pi / 4 + math.radians(origin.lat_deg) / 2)))
    return (point.lon_deg - origin.lon_deg) * scale, (y - y0) * scale


def _rhumb_bearing_deg(start: RoutePoint, end: RoutePoint) -> float:
    x, y = _mercator(end, start)
    return math.degrees(math.atan2(x, y)) % 360.0
