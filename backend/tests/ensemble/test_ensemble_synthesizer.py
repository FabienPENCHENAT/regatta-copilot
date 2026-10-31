import pytest

from sailrouter.ensemble.ensemble_synthesizer import EnsembleSynthesizer
from tests.ensemble.conftest import course, straight_route


def members(headings):
    return {f"p{k:02d}": straight_route(h) for k, h in enumerate(headings, start=1)}


def test_two_groups_give_two_options_with_member_shares_and_head_direction_advice():
    routes = members([200, 201, 202, 203, 204, 205, 206, 250, 251, 252])
    synthesis = EnsembleSynthesizer().synthesize(routes, game_route=straight_route(251), progress=course())
    first, second = synthesis.options
    assert (len(first.members), len(second.members)) == (7, 3)
    assert first.probability == pytest.approx(0.7) and second.probability == pytest.approx(0.3)
    assert synthesis.recommended is first and synthesis.member_total == 10
    assert first.representative == "p04"  # the middle of the fan (medoid)
    assert {first.id, second.id} <= {"direct", "north", "south", "west", "east"} and first.id != second.id
    assert [o.game_route for o in synthesis.options] == [False, True]
    assert synthesis.member_options["p09"] == second.id and synthesis.member_options["p01"] == first.id
    assert synthesis.advice == {"key": "advice.head_direction",
                                "params": {"option": first.id, "count": 7, "total": 10, "hours": 48}}
    assert sorted(first.confidence_by_hour) == [4, 8, 12, 16, 24, 48]
    assert first.confidence_by_hour[4] == 1.0 and 0.0 < second.confidence_by_hour[48] <= 1.0


def test_one_group_is_the_consensus():
    synthesis = EnsembleSynthesizer().synthesize(members([220, 221, 222]), straight_route(221), course())
    (option,) = synthesis.options
    assert (option.id, option.kind, option.probability, option.game_route) == ("consensus", "consensus", 1.0, True)
    assert synthesis.advice == {"key": "advice.consensus", "params": {"count": 3, "total": 3, "hours": 48}}
    assert option.eta_delta_h == 0.0
