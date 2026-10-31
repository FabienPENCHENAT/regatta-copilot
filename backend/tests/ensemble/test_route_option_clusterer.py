from datetime import timedelta

import pytest

from sailrouter.ensemble.route_distance_matrix import RouteDistanceMatrix
from sailrouter.ensemble.route_option_clusterer import RouteOptionClusterer
from sailrouter.routing.route import Route
from sailrouter.routing.route_point import RoutePoint
from tests.ensemble.conftest import T0, straight_route


def distances(headings):
    return RouteDistanceMatrix().distances_nm([straight_route(h) for h in headings])


def test_two_diverging_fans_make_two_options_largest_first():
    headings = [190, 192, 194, 196, 250, 252, 254]  # 480 nm sailed at 48 h: 2° apart ≈ 17 nm, 54° ≈ 435 nm
    groups = RouteOptionClusterer(threshold_nm=70).cluster(distances(headings))
    assert groups == [[0, 1, 2, 3], [4, 5, 6]]


def test_routes_close_together_make_one_option():
    assert RouteOptionClusterer().cluster(distances([220, 221, 222, 223])) == [[0, 1, 2, 3]]


def test_a_lone_member_joins_its_nearest_group():
    headings = [200, 201, 202, 240, 241, 242, 300]
    groups = RouteOptionClusterer(threshold_nm=70).cluster(distances(headings))
    assert groups == [[3, 4, 5, 6], [0, 1, 2]]


def test_never_more_than_max_options():
    headings = [180, 181, 200, 201, 220, 221, 240, 241, 260, 261]
    groups = RouteOptionClusterer(threshold_nm=70, max_options=4).cluster(distances(headings))
    assert len(groups) == 4 and sorted(i for g in groups for i in g) == list(range(10))


def test_routes_that_split_early_but_meet_at_48h_are_kept_apart():
    def route(lat_24h):
        points = tuple(RoutePoint(T0 + timedelta(hours=h), lat, -10.0, 0) for h, lat in ((0, 46.0), (24, lat_24h), (48, 44.0)))
        return Route(points, 2000.0, False)

    gap = RouteDistanceMatrix().distances_nm([route(45.0), route(45.5)])[0, 1]
    assert gap == pytest.approx(2 * 30.0, abs=0.1)  # same place at 48 h, 30 nm apart at 24 h, doubled
