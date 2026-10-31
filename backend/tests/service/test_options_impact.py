from datetime import UTC, datetime, timedelta

import numpy as np

from sailrouter.routing.route import Route
from sailrouter.routing.route_point import RoutePoint
from sailrouter.service.options_impact import OptionsImpact

START = datetime(2026, 11, 1, tzinfo=UTC)


class FakeProgress:
    def distance_to_go_nm(self, leg, lat, lon):
        return np.asarray(100.0 - lon * 60.0)  # going east: each 1/60° of longitude is one mile less to go


class FakeReport:
    def __init__(self, speed_kn):
        points = tuple(RoutePoint(START + timedelta(hours=h), 0.0, speed_kn * h / 60.0, 0) for h in range(0, 121, 24))
        self.route = Route(points, 0.0, False)
        self.progress = FakeProgress()


def test_gain_is_the_difference_in_distance_to_go():
    slow, fast = FakeReport(5.0), FakeReport(6.0)
    assert OptionsImpact._distance_to_go(slow, 24) - OptionsImpact._distance_to_go(fast, 24) == 24.0
    assert round(OptionsImpact._distance_to_go(slow, 120) - OptionsImpact._distance_to_go(fast, 120), 6) == 120.0
