from sailrouter.domain.geo_point import GeoPoint
from sailrouter.ensemble.option_labeler import OptionLabeler

ORIGIN = GeoPoint(46.0, -2.0)
COURSE = (ORIGIN, GeoPoint(16.0, -61.0))
EARLY, LATE = (46.0, -6.0), (46.0, -10.0)  # consensus track due west


def label(early, late):
    return OptionLabeler().label(early, late, EARLY, LATE, ORIGIN, COURSE)


def test_single_option_is_the_consensus():
    assert label([EARLY], [LATE]) == [("consensus", "consensus")]


def test_central_option_is_direct_and_the_others_take_their_side_of_a_westward_course():
    early = [(46.1, -6.0), (46.5, -6.0), (45.5, -6.0)]
    late = [(46.1, -10.0), (47.5, -10.0), (44.5, -10.0)]  # on the track, 90 nm right, 90 nm left
    assert [name for name, _ in label(early, late)] == ["direct", "north", "south"]


def test_early_split_counts_twice_like_the_grouping():
    early = [(46.0, -6.0), (45.2, -6.0)]  # second one is 48 nm south at 24 h...
    late = [(46.0, -10.0), (46.3, -10.0)]  # ...and 18 nm north at 48 h: south overall
    assert [name for name, _ in label(early, late)] == ["direct", "south"]


def test_two_options_on_one_side_get_the_side_then_the_heading_direction():
    early = [EARLY, (45.5, -6.0), (45.0, -6.0)]
    late = [LATE, (45.5, -10.0), (44.0, -10.0)]
    assert [name for name, _ in label(early, late)] == ["direct", "west", "south"]


def test_a_slightly_skewed_heading_still_prefers_the_heading_direction_for_the_inner_option():
    late_track = (45.7, -10.0)  # consensus heading 269.8°: east is 0.4° closer to "left" than west
    early = [EARLY, (45.5, -6.0), (45.0, -6.0)]
    late = [late_track, (45.5, -10.0), (44.0, -10.0)]
    names = [name for name, _ in OptionLabeler().label(early, late, EARLY, late_track, ORIGIN, COURSE)]
    assert names == ["direct", "west", "south"]


def test_no_direct_when_every_option_is_off_the_track():
    early = [(46.5, -6.0), (45.5, -6.0)]
    late = [(47.5, -10.0), (44.5, -10.0)]
    assert [name for name, _ in label(early, late)] == ["north", "south"]


def test_option_nearest_the_great_circle_is_the_shortest():
    course = (GeoPoint(46.0, -8.0), GeoPoint(16.0, -61.0))
    on_course, off_course = (44.63, -13.84), (42.0, -12.0)  # on the great circle 260 nm out / ≈ 120 nm off it
    labels = OptionLabeler().label([EARLY, EARLY], [off_course, on_course], EARLY, LATE, ORIGIN, course)
    assert [kind for _, kind in labels] == ["positioning", "shortest"]
