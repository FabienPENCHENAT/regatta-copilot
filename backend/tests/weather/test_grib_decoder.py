from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

from sailrouter.weather.grib_decoder import GribDecoder

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "gfs-small.grib2"


def test_decodes_nomads_subregion():
    # GFS 0.25° run 2026-10-31 06z, f003, 48–49°N / 3°W–2°W (5 × 5 points), as sent by the grib filter.
    grid = GribDecoder().decode(FIXTURE)
    assert grid.valid_time == datetime(2026, 10, 31, 9, tzinfo=UTC)
    assert np.allclose(grid.lat_deg, [48.0, 48.25, 48.5, 48.75, 49.0])
    assert np.allclose(grid.lon_deg, [-3.0, -2.75, -2.5, -2.25, -2.0])
    assert grid.u_ms.shape == (5, 5)
    assert grid.u_ms[0, 0] == pytest.approx(-4.354, abs=1e-3)
    assert grid.v_ms[-1, -1] == pytest.approx(-0.435, abs=1e-3)
