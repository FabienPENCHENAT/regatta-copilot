from datetime import UTC, datetime, timedelta

from sailrouter.routing.route import Route
from sailrouter.routing.route_leg_splitter import RouteLegSplitter
from sailrouter.routing.route_point import RoutePoint

START = datetime(2026, 11, 1, 12, tzinfo=UTC)


def route(*orders):
    """orders: (heading, twa, sail) for each hour; a final point closes the route."""
    points = [RoutePoint(START + timedelta(hours=h), 48.0, -2.0 - h * 0.1, 0, hdg, twa, 10.0 + h, sail, 8.0)
              for h, (hdg, twa, sail) in enumerate(orders)]
    points.append(RoutePoint(START + timedelta(hours=len(orders)), 48.0, -2.0 - len(orders) * 0.1, 0))
    return Route(tuple(points), distance_to_go_nm=100.0, finished=False)


def test_same_orders_make_one_leg_and_small_wobbles_are_ignored():
    legs = RouteLegSplitter().split(route((265, 146, "Spi"), (270, 141, "Spi"), (260, 150, "Spi")))
    assert len(legs) == 1
    assert legs[0].heading_deg == 265 and legs[0].end == START + timedelta(hours=3)
    assert (legs[0].tws_min_kn, legs[0].tws_max_kn) == (10.0, 12.0)


def test_a_new_leg_on_heading_change_sail_change_and_gybe():
    legs = RouteLegSplitter().split(route(
        (265, 146, "Spi"), (265, 146, "Spi"),   # 2 h
        (280, 131, "Spi"),                      # turned 15°
        (280, 100, "Jib"),                      # sail change
        (280, -150, "Jib"),                     # gybe: wind on the other side
    ))
    assert [(leg.heading_deg, leg.sail, (leg.end - leg.start).seconds // 3600) for leg in legs] == [
        (265, "Spi", 2), (280, "Spi", 1), (280, "Jib", 1), (280, "Jib", 1),
    ]
