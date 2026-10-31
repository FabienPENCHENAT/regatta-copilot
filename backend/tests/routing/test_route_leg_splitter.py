import math
from datetime import UTC, datetime, timedelta

import pytest

from sailrouter.routing.route import Route
from sailrouter.routing.route_leg_splitter import RouteLegSplitter
from sailrouter.routing.route_point import RoutePoint

START = datetime(2026, 11, 1, 12, tzinfo=UTC)
LAT = 48.0


def route(*steps):
    """steps: (heading, twa, sail) for each hour at 6 kn from (48°N, 2°W); a final point closes the route."""
    points, lat, lon = [], LAT, -2.0
    for hour, (heading, twa, sail) in enumerate(steps):
        points.append(RoutePoint(START + timedelta(hours=hour), lat, lon, 0, heading, twa, 10.0 + hour, sail, 6.0))
        lat += 6.0 / 60 * math.cos(math.radians(heading))
        lon += 6.0 / 60 * math.sin(math.radians(heading)) / math.cos(math.radians(LAT))
    points.append(RoutePoint(START + timedelta(hours=len(steps)), lat, lon, 0))
    return Route(tuple(points), distance_to_go_nm=100.0, finished=False)


def test_a_straight_route_is_one_order_with_its_true_heading():
    legs = RouteLegSplitter().split(route(*[(270, 140, "Spi")] * 4))
    assert len(legs) == 1
    assert legs[0].heading_deg == pytest.approx(270, abs=0.5) and legs[0].end == START + timedelta(hours=4)
    assert (legs[0].tws_min_kn, legs[0].tws_max_kn) == (10.0, 13.0)


def test_a_slow_turn_is_cut_before_the_straight_line_drifts_off_the_route():
    # 3° more every hour: after a few hours one constant heading would leave the route by more than 0.5 nm
    legs = RouteLegSplitter().split(route(*[(270 + 3 * h, 140 - 3 * h, "Spi") for h in range(12)]))
    assert len(legs) > 1
    assert all(abs(b.heading_deg - a.heading_deg) < 20 for a, b in zip(legs, legs[1:]))


def test_small_zigzags_are_one_order_but_sails_and_gybes_always_cut():
    wobble = RouteLegSplitter().split(route((268, 140, "Spi"), (272, 136, "Spi"), (268, 140, "Spi")))
    assert len(wobble) == 1
    legs = RouteLegSplitter().split(route(
        (265, 146, "Spi"), (265, 146, "Spi"),   # 2 h
        (265, 100, "Jib"),                      # sail change
        (265, -150, "Jib"),                     # gybe: wind on the other side
    ))
    assert [(leg.sail, (leg.end - leg.start).seconds // 3600) for leg in legs] == [("Spi", 2), ("Jib", 1), ("Jib", 1)]
