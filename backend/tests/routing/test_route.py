from datetime import UTC, datetime, timedelta

import pytest

from sailrouter.routing.route import Route
from sailrouter.routing.route_point import RoutePoint

T0 = datetime(2026, 11, 1, 12, tzinfo=UTC)


def make_route():
    points = tuple(RoutePoint(T0 + timedelta(hours=h), 46.0 - 0.1 * h, -8.0 - 0.2 * h, 0) for h in (0, 1, 2, 5))
    return Route(points, 2000.0, False)


def test_position_is_interpolated_between_route_points_and_held_after_the_end():
    route = make_route()
    assert route.position_at(0) == (46.0, -8.0)
    assert route.position_at(3.5) == pytest.approx((46.0 - 0.35, -8.0 - 0.7))
    assert route.position_at(9) == pytest.approx((45.5, -9.0))
    assert route.duration_h == 5.0
