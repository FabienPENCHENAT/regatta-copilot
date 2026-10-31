from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from sailrouter.weather.wind_field import MS_TO_KN, WindField
from sailrouter.weather.wind_grid import WindGrid

T0 = datetime(2026, 11, 1, 12, tzinfo=UTC)
LAT = np.array([40.0, 41.0, 42.0])
LON = np.array([-10.0, -9.0, -8.0])


def grid(hours: float, u, v) -> WindGrid:
    shape = (LAT.size, LON.size)
    return WindGrid(
        T0 + timedelta(hours=hours), LAT, LON,
        np.broadcast_to(np.asarray(u, np.float32), shape).copy(),
        np.broadcast_to(np.asarray(v, np.float32), shape).copy(),
    )


def test_direction_is_where_the_wind_comes_from():
    # v > 0 blows towards the north: a southerly wind, from 180°. u > 0: westerly, from 270°.
    for u, v, expected in [(0, 5, 180.0), (0, -5, 0.0), (5, 0, 270.0), (-5, 0, 90.0)]:
        tws, twd = WindField([grid(0, u, v), grid(3, u, v)]).wind_at(41.0, -9.0, T0.timestamp())
        assert twd == pytest.approx(expected)
        assert tws == pytest.approx(5 * MS_TO_KN)


def test_bilinear_in_space():
    u = np.array([[0, 2, 4], [0, 2, 4], [0, 2, 4]], np.float32)  # u grows eastward: 2 m/s per degree
    field = WindField([WindGrid(T0, LAT, LON, u, np.zeros_like(u))])
    tws, _ = field.wind_at(np.array([40.5, 41.25]), np.array([-9.5, -8.25]), T0.timestamp())
    assert tws == pytest.approx(np.array([1.0, 3.5]) * MS_TO_KN)


def test_linear_in_time_on_components():
    field = WindField([grid(0, 0, 10), grid(3, 0, 4)])
    tws, _ = field.wind_at(41.0, -9.0, (T0 + timedelta(hours=1)).timestamp())
    assert tws == pytest.approx(8 * MS_TO_KN)


def test_clamps_outside_space_and_time():
    field = WindField([grid(0, 0, 10), grid(3, 0, 4)])
    tws, _ = field.wind_at(80.0, 50.0, (T0 + timedelta(hours=10)).timestamp())
    assert tws == pytest.approx(4 * MS_TO_KN)
    assert field.first_time == T0 and field.last_time == T0 + timedelta(hours=3)


def test_rejects_grids_on_different_coordinates():
    other = WindGrid(T0, LAT + 1, LON, np.zeros((3, 3), np.float32), np.zeros((3, 3), np.float32))
    with pytest.raises(ValueError):
        WindField([grid(0, 0, 1), other])
