from sailrouter.domain.geo_point import GeoPoint
from sailrouter.ensemble.option_labeler import OptionLabeler

ORIGIN = GeoPoint(0.0, -2.0)
MARK_WEST = GeoPoint(0.0, -40.0)
COURSE = (ORIGIN, MARK_WEST)  # next mark due west, along the equator: a straight line on the chart
EARLY, LATE = (0.0, -6.0), (0.0, -10.0)  # on the line to the mark


def names(early, late, course=COURSE):
    return [name for name, _ in OptionLabeler().label(early, late, course[0], course)]


def test_single_option_is_the_consensus():
    assert OptionLabeler().label([EARLY], [LATE], ORIGIN, COURSE) == [("consensus", "consensus")]


def test_central_option_is_direct_and_the_others_take_their_side_of_a_westward_course():
    early = [(0.1, -6.0), (0.5, -6.0), (-0.5, -6.0)]
    late = [(0.1, -10.0), (1.5, -10.0), (-1.5, -10.0)]  # on the line, 90 nm right, 90 nm left
    assert names(early, late) == ["direct", "north", "south"]


def test_early_split_counts_twice_like_the_grouping():
    early = [(0.0, -6.0), (-0.8, -6.0)]  # second one is 48 nm south at 24 h...
    late = [(0.0, -10.0), (0.3, -10.0)]  # ...and 18 nm north at 48 h: south overall
    assert names(early, late) == ["direct", "south"]


def test_two_options_on_one_side_are_the_side_then_the_wide_side():
    early = [EARLY, (-0.5, -6.0), (-1.0, -6.0)]
    late = [LATE, (-0.5, -10.0), (-2.0, -10.0)]
    assert names(early, late) == ["direct", "south", "south_wide"]


def test_three_options_on_one_side_without_a_direct_one():
    early = [(1.0, -6.0), (1.5, -6.0), (2.0, -6.0)]
    late = [(2.0, -10.0), (3.0, -10.0), (4.0, -10.0)]
    assert names(early, late) == ["north", "north_wide", "north_far"]


def test_no_direct_when_every_option_is_off_the_line():
    early = [(0.8, -6.0), (-0.8, -6.0)]
    late = [(2.0, -10.0), (-2.0, -10.0)]  # about 55 nm off on average
    assert names(early, late) == ["north", "south"]


def test_an_option_slowly_drifting_off_the_line_is_still_the_direct_one():
    early = [(0.2, -6.0), (-1.0, -6.0)]
    late = [(1.1, -10.0), (-2.0, -10.0)]  # 12 nm then 66 nm off, like a route bending away late
    assert names(early, late) == ["direct", "south"]


def test_names_follow_the_line_to_the_mark_not_the_options_themselves():
    # every option goes north of the line: the most central one is not "direct" for all that
    early = [(0.8, -6.0), (1.4, -6.0)]
    late = [(1.8, -10.0), (2.6, -10.0)]
    assert names(early, late) == ["north", "north_wide"]


def test_on_a_southward_course_the_sides_are_west_and_east():
    course = (GeoPoint(46.0, -2.0), GeoPoint(16.0, -2.0))  # down a meridian
    early = [(44.0, -2.0), (44.0, -2.8), (44.0, -1.2)]
    late = [(42.0, -2.0), (42.0, -4.0), (42.0, 0.0)]
    assert names(early, late, course) == ["direct", "west", "east"]


def test_option_nearest_the_great_circle_is_the_shortest():
    course = (GeoPoint(46.0, -8.0), GeoPoint(16.0, -61.0))
    on_course, off_course = (44.63, -13.84), (42.0, -12.0)  # on the great circle 260 nm out / ≈ 120 nm off it
    labels = OptionLabeler().label([EARLY, EARLY], [off_course, on_course], ORIGIN, course)
    assert [kind for _, kind in labels] == ["positioning", "shortest"]
