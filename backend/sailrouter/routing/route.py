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

    def position_at(self, hours: float) -> tuple[float, float]:
        """(lat, lon) at `start + hours`, linear between route points (hourly for 24 h, 3-hourly after);
        the last position once the route has ended."""
        moment = self.start + timedelta(hours=hours)
        after = next((i for i, p in enumerate(self.points) if p.time >= moment), len(self.points) - 1)
        before = max(after - 1, 0)
        a, b = self.points[before], self.points[after]
        span = (b.time - a.time).total_seconds()
        weight = min(max((moment - a.time).total_seconds() / span, 0.0), 1.0) if span > 0 else 1.0
        return a.lat_deg + weight * (b.lat_deg - a.lat_deg), a.lon_deg + weight * (b.lon_deg - a.lon_deg)

    @property
    def duration_h(self) -> float:
        return (self.end - self.start) / timedelta(hours=1)

    def covers(self, hours: float) -> bool:
        return self.end >= self.start + timedelta(hours=hours) - timedelta(seconds=1)
