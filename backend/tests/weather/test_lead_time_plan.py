import pytest

from sailrouter.weather.lead_time_plan import LeadTimePlan


def test_gfs_plan_is_hourly_then_three_hourly():
    leads = LeadTimePlan().all_lead_hours()
    assert leads[:3] == [0, 1, 2]
    assert leads[120:123] == [120, 123, 126]
    assert leads[-1] == 384


def test_window_is_bracketed():
    plan = LeadTimePlan()
    assert plan.lead_hours_covering(30.03, 33.5) == [30, 31, 32, 33, 34]
    leads = plan.lead_hours_covering(118.5, 125.0)
    assert leads == [118, 119, 120, 123, 126]


def test_gefs_plan_is_three_hourly():
    assert LeadTimePlan(hourly_until_h=0).lead_hours_covering(4, 8) == [3, 6, 9]


def test_window_outside_forecast_is_refused():
    with pytest.raises(ValueError):
        LeadTimePlan().lead_hours_covering(-1, 5)


def test_the_game_reads_gfs_every_3_hours():
    plan = LeadTimePlan.game()
    assert plan.all_lead_hours()[:4] == [0, 3, 6, 9] and plan.all_lead_hours()[-1] == 384
    assert plan.lead_hours_covering(13.9, 20.0) == [12, 15, 18, 21]
