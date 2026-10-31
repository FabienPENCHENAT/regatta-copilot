from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sailrouter.routing.route import Route
from sailrouter.routing.route_point import RoutePoint


@dataclass(frozen=True)
class RouteLeg:
    """A stretch of the route sailed with the same orders: one heading (within tolerance), one sail, one tack."""

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
    """Cuts a route into legs: a new leg starts on a sail change, a tack or gybe (the wind changes side), or a
    heading change of at least `heading_tolerance_deg` from the leg's first heading. This is the route plan the
    player types into the game, order by order."""

    def __init__(self, heading_tolerance_deg: float = 10.0) -> None:
        self._tolerance = heading_tolerance_deg

    def split(self, route: Route) -> list[RouteLeg]:
        sailed = [p for p in route.points if p.heading_deg is not None]
        if not sailed:
            return []
        groups: list[list[RoutePoint]] = [[sailed[0]]]
        for point in sailed[1:]:
            if self._new_orders(groups[-1][0], point):
                groups.append([point])
            else:
                groups[-1].append(point)
        ends = [group[0] for group in groups[1:]] + [route.points[-1]]
        return [self._leg(group, end) for group, end in zip(groups, ends)]

    def _new_orders(self, first: RoutePoint, point: RoutePoint) -> bool:
        turned = abs((point.heading_deg - first.heading_deg + 180.0) % 360.0 - 180.0) >= self._tolerance
        other_side = (point.twa_deg >= 0) != (first.twa_deg >= 0)
        return point.sail != first.sail or other_side or turned

    @staticmethod
    def _leg(points: list[RoutePoint], end: RoutePoint) -> RouteLeg:
        first = points[0]
        winds = [p.tws_kn for p in points]
        return RouteLeg(
            start=first.time, end=end.time, start_point=first, end_point=end,
            heading_deg=first.heading_deg, sail=first.sail, twa_deg=first.twa_deg,
            tws_min_kn=min(winds), tws_max_kn=max(winds),
            speed_kn=sum(p.speed_kn for p in points) / len(points),
        )
