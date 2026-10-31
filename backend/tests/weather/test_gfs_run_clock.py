from datetime import UTC, datetime

from sailrouter.weather.gfs_query_builder import GfsQueryBuilder
from sailrouter.weather.gfs_run_clock import GfsRunClock
from sailrouter.weather.weather_area import WeatherArea


def test_latest_complete_run_waits_for_the_availability_delay():
    clock = GfsRunClock()
    assert clock.latest_complete(datetime(2026, 10, 31, 9, 39, tzinfo=UTC)).key == "gfs-2026103100"
    assert clock.latest_complete(datetime(2026, 10, 31, 9, 40, tzinfo=UTC)).key == "gfs-2026103106"  # 3 h 40
    assert clock.latest_complete(datetime(2026, 10, 31, 3, 0, tzinfo=UTC)).key == "gfs-2026103018"
    run = clock.latest_complete(datetime(2026, 10, 31, 17, 0, tzinfo=UTC))
    assert run.key == "gfs-2026103112"
    assert clock.previous(run).key == "gfs-2026103106"
    assert clock.next_expected(run) == datetime(2026, 10, 31, 21, 40, tzinfo=UTC)
    assert GfsRunClock(model="gefs").next_expected(run) == datetime(2026, 10, 31, 23, tzinfo=UTC)


def test_query_for_one_lead_time():
    run = GfsRunClock().latest_complete(datetime(2026, 10, 31, 12, 59, tzinfo=UTC))
    script, params = GfsQueryBuilder(WeatherArea()).query(run, 24)
    assert script == "filter_gfs_0p25.pl"
    assert params["dir"] == "/gfs.20261031/06/atmos"
    assert params["file"] == "gfs.t06z.pgrb2.0p25.f024"
    assert (params["toplat"], params["leftlon"], params["rightlon"], params["bottomlat"]) == ("60", "-80", "10", "0")
