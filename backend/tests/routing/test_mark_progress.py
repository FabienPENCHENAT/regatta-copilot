from pathlib import Path

import numpy as np
import pytest

from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.mark import Mark
from sailrouter.domain.race import Race
from sailrouter.routing.course_leg import CourseLeg
from sailrouter.routing.mark_progress import MarkProgress

RACES = Path(__file__).resolve().parents[3] / "races"
GUADELOUPE_MARKS = ["tete_anglais", "basse_terre_buoy", "les_saintes", "pointe_a_pitre_buoy"]


@pytest.fixture(scope="module")
def race() -> Race:
    return RaceCatalog(RACES).load("route-du-rhum-2026")


@pytest.fixture(scope="module")
def progress(race):
    return MarkProgress.from_race(race, GeoPoint(48.73, -1.9))


def _leg_index(progress: MarkProgress, mark_id: str) -> int:
    return [leg.mark_id for leg in progress.legs].index(mark_id)


def _advance(progress, mark_id, lat0, lon0, lat1, lon1) -> list[bool]:
    """Whether each segment passes `mark_id` (segments given as lists)."""
    k = _leg_index(progress, mark_id)
    arrays = [np.asarray(values, float) for values in (lat0, lon0, lat1, lon1)]
    leg = np.full(arrays[0].size, k, dtype=np.int16)
    return (progress.advance(leg, *arrays) == k + 1).tolist()


def test_legs_follow_the_whole_course(progress):
    ids = [leg.mark_id for leg in progress.legs]
    assert ids == [*GUADELOUPE_MARKS, "finish"]
    assert progress.legs[1].anchor == progress.legs[0].target


def test_rounding_marks_are_aimed_at_the_physical_mark(progress, race):
    tete = progress.legs[_leg_index(progress, "tete_anglais")]
    assert (tete.target.lat_deg, tete.target.lon_deg) == pytest.approx((16.380833, -61.764167))
    assert tete.line is not None and tete.cross == "southward"
    assert race.mark("les_saintes").target == GeoPoint(15.861, -61.61)


def test_gate_must_be_crossed_westward():
    gate = (GeoPoint(48.696667, -2.308333), GeoPoint(48.713333, -2.308333))  # a 1 nm gate off a cape
    progress = MarkProgress([CourseLeg("gate", GeoPoint(48.72, -2.14), gate[0], gate, "westward")])
    # westward through the gate, eastward through it, westward north of the gate
    assert _advance(progress, "gate", [48.705, 48.705, 48.75], [-2.25, -2.35, -2.25],
                    [48.705, 48.705, 48.75], [-2.35, -2.25, -2.35]) == [True, False, False]


def test_tete_anglais_counts_only_west_of_the_islet_southbound(progress):
    # southbound west of the islet, southbound EAST of it (wrong side), northbound west of it (wrong way)
    assert _advance(progress, "tete_anglais", [16.45, 16.45, 16.30], [-61.80, -61.70, -61.80],
                    [16.30, 16.30, 16.45], [-61.80, -61.70, -61.80]) == [True, False, False]


def test_basse_terre_buoy_counts_only_between_buoy_and_coast(progress):
    # southbound between the buoy and the coast, southbound west of the buoy (buoy left to port)
    assert _advance(progress, "basse_terre_buoy", [16.0, 16.0], [-61.735, -61.75],
                    [15.975, 15.975], [-61.735, -61.75]) == [True, False]


def test_les_saintes_count_only_when_passed_to_the_north(progress):
    # eastbound through the Canal des Saintes, eastbound south of the archipelago, westbound in the canal
    assert _advance(progress, "les_saintes", [15.94, 15.82, 15.94], [-61.65, -61.65, -61.55],
                    [15.94, 15.82, 15.94], [-61.55, -61.55, -61.65]) == [True, False, False]


def test_pointe_a_pitre_buoy_counts_only_when_left_to_port(progress):
    # northbound east of the buoy, northbound west of it
    assert _advance(progress, "pointe_a_pitre_buoy", [16.14, 16.14], [-61.51, -61.53],
                    [16.18, 16.18], [-61.51, -61.53]) == [True, False]


def test_waypoint_reached_within_radius():
    start, target = GeoPoint(10.0, -30.0), GeoPoint(10.0, -40.0)
    progress = MarkProgress([CourseLeg("buoy", start, target, radius_nm=2.0)])
    lat = np.array([target.lat_deg + 0.02, target.lat_deg + 0.2])
    lon0, lon1 = np.full(2, target.lon_deg - 0.3), np.full(2, target.lon_deg + 0.3)
    assert progress.advance(np.zeros(2, dtype=np.int16), lat, lon0, lat, lon1).tolist() == [1, 0]


def test_distance_to_go_adds_the_remaining_legs(progress):
    start = GeoPoint(48.718, -2.144)
    to_go = progress.distance_to_go_nm(np.array([0]), np.array([start.lat_deg]), np.array([start.lon_deg]))
    assert 3400 < to_go[0] < 3600  # Saint-Malo → Guadeloupe, great circle, then around the island


def test_a_finishing_segment_stops_on_the_finish_line(progress):
    k = progress.finished_leg - 1
    lat0, lon0, lat1, lon1 = (np.array([v]) for v in (16.19, -61.515, 16.25, -61.515))
    old = np.array([k])
    new = progress.advance(old, lat0, lon0, lat1, lon1)
    assert new[0] == progress.finished_leg
    end_lat, end_lon = progress.end_at_finish(old, new, lat0, lon0, lat1, lon1)
    assert (end_lat[0], end_lon[0]) == pytest.approx((16.2, -61.515))


def test_unknown_mark_kind_is_refused():
    with pytest.raises(ValueError):
        Mark("x", "island", (GeoPoint(16.0, -61.6),))
