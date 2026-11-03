from datetime import UTC, datetime

import numpy as np
import pytest

from sailrouter.domain.geo_point import GeoPoint
from sailrouter.routing.course_leg import CourseLeg
from sailrouter.routing.mark_progress import MarkProgress
from sailrouter.routing.time_schedule import TimeSchedule
from sailrouter.routing.track_follower import TrackFollower

START = datetime(2026, 11, 1, tzinfo=UTC)


class SteadyWind:
    def __init__(self, from_deg):
        self.from_deg = from_deg

    def wind_at(self, lat, lon, time_s):
        return np.full(np.shape(lat), 15.0), np.full(np.shape(lat), self.from_deg)


class TenKnots:
    """10 kn at any angle except within 40° of the wind (no-go)."""

    sail_names = ("Jib",)

    def best(self, tws, twa):
        twa = np.abs(np.asarray(twa, float))
        return np.zeros(twa.shape, dtype=np.int8), np.where(twa < 40, 0.0, 10.0)


def _follower():
    target = GeoPoint(0.0, -10.0)
    return TrackFollower(TenKnots(), MarkProgress([CourseLeg("mark", GeoPoint(0.0, 0.0), target, radius_nm=1.0)]))


TRACK = [(0.0, -lon / 60, 0) for lon in range(0, 200, 10)]  # due west along the equator


def _follow(wind_from):
    return _follower().distances_to_go(TRACK, SteadyWind(wind_from), START, [10.0])[10.0]


def test_a_beam_reach_follows_the_track_at_full_speed():
    assert _follow(wind_from=0.0) == pytest.approx(600.0 - 100.0, abs=0.5)  # 10 h at 10 kn towards the mark


def test_dead_upwind_the_boat_tacks_instead_of_stopping():
    made_good = 600.0 - _follow(wind_from=270.0)
    assert 60.0 < made_good < 100.0  # beats at 45° off the wind: about 10 × cos 45° per hour


def test_the_track_sailed_in_another_weather_gives_the_settings_of_that_weather():
    route = _follower().route(TRACK, SteadyWind(0.0), TimeSchedule(START, 2.0))
    first = route.points[0]
    assert (first.heading_deg, first.twa_deg, first.tws_kn, first.sail, first.speed_kn) == pytest.approx(
        (270.0, 90.0, 15.0, "Jib", 10.0))
    assert route.points[-1].time == START.replace(hour=2)
    assert route.points[-1].lon_deg == pytest.approx(-20 / 60, abs=1e-3)  # 2 h at 10 kn
    assert route.distance_to_go_nm == pytest.approx(580.0, abs=0.5)
