from pathlib import Path

import numpy as np
import pytest

from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.routing.mark_progress import MarkProgress

RACES = Path(__file__).resolve().parents[3] / "races"


@pytest.fixture(scope="module")
def progress():
    race = RaceCatalog(RACES).load("route-du-rhum-2026")
    return MarkProgress.from_race(race, GeoPoint(48.73, -1.9))


def test_legs_follow_the_course_without_islands(progress):
    ids = [leg.mark_id for leg in progress.legs]
    assert ids == ["frehel_gate", "tete_anglais", "basse_terre_buoy", "pointe_a_pitre_buoy", "finish"]
    assert progress.legs[1].anchor == progress.legs[0].target


def test_gate_must_be_crossed_westward(progress):
    leg = np.zeros(3, dtype=np.int16)
    lat0 = np.array([48.705, 48.705, 48.75])
    lon0 = np.array([-2.25, -2.35, -2.25])
    lat1 = np.array([48.705, 48.705, 48.75])
    lon1 = np.array([-2.35, -2.25, -2.35])
    # westward through the gate, eastward through it, westward north of the gate
    assert progress.advance(leg, lat0, lon0, lat1, lon1).tolist() == [1, 0, 0]


def test_waypoint_reached_within_radius(progress):
    leg = np.array([1, 1], dtype=np.int16)
    target = progress.legs[1].target
    lat = np.array([target.lat_deg + 0.02, target.lat_deg + 0.2])
    lon0, lon1 = np.full(2, target.lon_deg - 0.3), np.full(2, target.lon_deg + 0.3)
    assert progress.advance(leg, lat, lon0, lat, lon1).tolist() == [2, 1]


def test_distance_to_go_adds_the_remaining_legs(progress):
    at_gate = progress.legs[0].target
    to_go = progress.distance_to_go_nm(np.array([0]), np.array([at_gate.lat_deg]), np.array([at_gate.lon_deg]))
    assert 3400 < to_go[0] < 3600  # Fréhel → Guadeloupe, great circle, then around the island
