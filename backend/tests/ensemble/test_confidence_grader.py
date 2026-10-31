import pytest

from sailrouter.ensemble.confidence_grader import ConfidenceGrader
from tests.ensemble.conftest import straight_route


def test_zone_radius_grows_with_the_hour():
    assert [ConfidenceGrader.zone_radius_nm(h) for h in (4, 12, 24, 48)] == [7, 14, 25, 46]


def test_confidence_is_the_share_of_members_inside_the_zone():
    representative = straight_route(220)
    members = [straight_route(h) for h in (220, 221, 230)]  # 10° apart: 3.5 nm at 2 h, 84 nm at 48 h
    grader = ConfidenceGrader()
    assert grader.confidence(representative, members, 2) == pytest.approx(1.0)
    assert grader.confidence(representative, members, 48) == pytest.approx(2 / 3)
    assert grader.confidence(representative, [], 12) == 0.0
