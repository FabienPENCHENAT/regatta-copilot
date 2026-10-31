import numpy as np
import pytest

from sailrouter.domain.great_circle import GreatCircle


def test_cross_track_is_signed_positive_right_of_the_course():
    # course due north along 10°W; one degree of longitude near the equator is ≈ 60 nm
    assert GreatCircle.cross_track_nm(0.0, -10.0, 10.0, -10.0, 5.0, -9.0) == pytest.approx(59.8, abs=0.3)
    assert GreatCircle.cross_track_nm(0.0, -10.0, 10.0, -10.0, 5.0, -11.0) == pytest.approx(-59.8, abs=0.3)
    assert GreatCircle.cross_track_nm(0.0, -10.0, 10.0, -10.0, 5.0, -10.0) == pytest.approx(0.0, abs=1e-6)


def test_one_degree_of_latitude_is_sixty_nautical_miles():
    assert GreatCircle.distance_nm(45.0, -10.0, 46.0, -10.0) == pytest.approx(60.04, abs=0.05)


def test_bearing_to_cardinal_points():
    bearings = GreatCircle.bearing_deg(0.0, 0.0, np.array([1.0, 0.0, -1.0, 0.0]), np.array([0.0, 1.0, 0.0, -1.0]))
    assert bearings == pytest.approx([0.0, 90.0, 180.0, 270.0])


def test_destination_round_trip_is_vectorised():
    lat0 = np.array([48.7, 16.2, 30.0])
    lon0 = np.array([-2.3, -61.5, -40.0])
    bearing = np.array([265.0, 45.0, 180.0])
    lat1, lon1 = GreatCircle.destination(lat0, lon0, bearing, 120.0)
    assert GreatCircle.distance_nm(lat0, lon0, lat1, lon1) == pytest.approx(120.0)
    assert GreatCircle.bearing_deg(lat0, lon0, lat1, lon1) == pytest.approx(bearing, abs=1e-6)


def test_destination_normalises_longitude():
    _, lon = GreatCircle.destination(0.0, 179.9, 90.0, 60.0)
    assert -180.0 <= lon < -179.0
