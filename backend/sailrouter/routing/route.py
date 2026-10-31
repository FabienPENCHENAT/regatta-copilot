from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sailrouter.routing.route_point import RoutePoint


@dataclass(frozen=True)
class Route:
    """The best route found: ordered `RoutePoint`s from the start, plus its distance to go at the end."""

    points: tuple[RoutePoint, ...]
    distance_to_go_nm: float
    finished: bool

    @property
    def start(self) -> datetime:
        return self.points[0].time

    @property
    def end(self) -> datetime:
        return self.points[-1].time

    def point_at(self, hours: float) -> RoutePoint:
        """The last route point at or before `start + hours` (the route plan uses the steps' own times)."""
        moment = self.start + timedelta(hours=hours) + timedelta(seconds=1)
        reached = [point for point in self.points if point.time <= moment]
        return reached[-1]

    def covers(self, hours: float) -> bool:
        return self.end >= self.start + timedelta(hours=hours) - timedelta(seconds=1)
