"""Synthetic member routes: straight lines from one start, hourly to 24 h then 3-hourly, like the router's."""

from datetime import UTC, datetime, timedelta

from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.great_circle import GreatCircle
from sailrouter.routing.course_leg import CourseLeg
from sailrouter.routing.mark_progress import MarkProgress
from sailrouter.routing.route import Route
from sailrouter.routing.route_point import RoutePoint

T0 = datetime(2026, 11, 1, 12, tzinfo=UTC)
START = (46.0, -8.0)
TARGET = GeoPoint(16.0, -61.0)  # far south-west, like Guadeloupe from Brittany
HOURS = [*range(0, 24), *range(24, 61, 3)]


def straight_route(heading_deg: float, speed_kn: float = 10.0, to_go_nm: float = 2500.0, sail: str = "Spi") -> Route:
    points = []
    for k, hour in enumerate(HOURS):
        lat, lon = GreatCircle.destination(START[0], START[1], heading_deg, speed_kn * hour)
        last = k == len(HOURS) - 1
        settings = {} if last else dict(heading_deg=heading_deg, twa_deg=140.0, tws_kn=15.0, sail=sail,
                                        speed_kn=speed_kn)
        points.append(RoutePoint(T0 + timedelta(hours=hour), float(lat), float(lon), 0, **settings))
    return Route(tuple(points), to_go_nm, False)


def course() -> MarkProgress:
    return MarkProgress([CourseLeg("guadeloupe", GeoPoint(*START), TARGET, None, None, 2.0)])
