import pytest

from sailrouter.ensemble.eta_gap_estimator import EtaGapEstimator
from tests.ensemble.conftest import straight_route


def test_arrival_is_extrapolated_with_the_route_mean_speed():
    route = straight_route(220, speed_kn=10.0, to_go_nm=1000.0)  # 60 h sailed at 10 kn
    assert EtaGapEstimator.eta_h(route) == pytest.approx(60 + 100, abs=0.1)


def test_gaps_are_relative_to_the_earliest_arrival():
    fast = straight_route(220, speed_kn=10.0, to_go_nm=1000.0)
    slow = straight_route(250, speed_kn=10.0, to_go_nm=1100.0)
    assert EtaGapEstimator().gaps_h([slow, fast]) == pytest.approx([10.0, 0.0], abs=0.1)
