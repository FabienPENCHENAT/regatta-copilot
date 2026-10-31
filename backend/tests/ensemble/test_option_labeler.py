from sailrouter.domain.geo_point import GeoPoint
from sailrouter.ensemble.option_labeler import OptionLabeler

COURSE = (GeoPoint(46.0, -8.0), GeoPoint(16.0, -61.0))
CONSENSUS = (42.0, -12.0)


def test_single_option_is_the_consensus():
    assert OptionLabeler().label([(42.0, -12.0)], CONSENSUS, COURSE) == [("consensus", "consensus")]


def test_option_at_the_consensus_is_direct_and_others_take_their_compass_side():
    positions = [(42.1, -12.1), (44.0, -12.0), (40.0, -12.2)]  # at consensus, 120 nm north, 120 nm south
    ids = [name for name, _ in OptionLabeler().label(positions, CONSENSUS, COURSE)]
    assert ids == ["direct", "north", "south"]


def test_two_options_on_the_same_side_get_different_names():
    positions = [(44.0, -11.5), (44.5, -12.5)]  # both north of the consensus, the second slightly west
    ids = [name for name, _ in OptionLabeler().label(positions, CONSENSUS, COURSE)]
    assert ids[0] == "north" and ids[1] in ("west", "east") and len(set(ids)) == 2


def test_option_nearest_the_great_circle_is_the_shortest():
    on_course = (44.63, -13.84)  # on the great circle Brittany → Guadeloupe, 260 nm from the start
    off_course = (42.0, -12.0)  # ≈ 120 nm off the course
    labels = OptionLabeler().label([off_course, on_course], CONSENSUS, COURSE)
    assert [kind for _, kind in labels] == ["positioning", "shortest"]
