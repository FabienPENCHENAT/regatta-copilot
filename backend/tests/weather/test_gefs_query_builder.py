from datetime import UTC, datetime

import pytest

from sailrouter.weather.gefs_query_builder import GEFS_MEMBERS, GefsQueryBuilder
from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.weather_area import WeatherArea


def test_members_are_the_control_and_thirty_perturbed_runs():
    assert len(GEFS_MEMBERS) == 31 and GEFS_MEMBERS[0] == "c00" and GEFS_MEMBERS[-1] == "p30"


def test_query_names_the_member_file_of_the_half_degree_ensemble():
    run = ModelRun("gefs", datetime(2026, 10, 31, 6, tzinfo=UTC))
    script, params = GefsQueryBuilder(WeatherArea()).query(run, 30, "p07")
    assert script == "filter_gefs_atmos_0p50a.pl"
    assert params["dir"] == "/gefs.20261031/06/atmos/pgrb2ap5"
    assert params["file"] == "gep07.t06z.pgrb2a.0p50.f030"
    assert GefsQueryBuilder(WeatherArea()).query(run, 3, "c00")[1]["file"] == "gec00.t06z.pgrb2a.0p50.f003"
    assert (params["toplat"], params["leftlon"], params["rightlon"], params["bottomlat"]) == ("60", "-80", "10", "0")
    assert params["var_UGRD"] == params["var_VGRD"] == params["lev_10_m_above_ground"] == "on"


def test_unknown_member_is_refused():
    run = ModelRun("gefs", datetime(2026, 10, 31, 6, tzinfo=UTC))
    with pytest.raises(ValueError):
        GefsQueryBuilder(WeatherArea()).query(run, 0, "p31")
