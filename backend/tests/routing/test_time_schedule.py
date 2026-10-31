from datetime import UTC, datetime

from sailrouter.routing.time_schedule import TimeSchedule

START = datetime(2026, 11, 1, 12, 2, tzinfo=UTC)


def test_quarter_hours_first_then_coarser():
    hours = TimeSchedule(START, 120).elapsed_hours()
    assert hours[:3] == [0, 0.25, 0.5]
    assert 5.75 in hours and 6.5 in hours and 6.25 not in hours  # 15 min until +6 h, then 30 min
    assert 25 in hours and 24.5 not in hours  # 1 h from +24 h
    assert 51 in hours and 49 not in hours  # 3 h from +48 h
    assert hours[-1] == 120
    assert len(hours) - 1 == 24 + 36 + 24 + 24
    assert {4, 8, 12, 16, 24, 48} <= set(hours)


def test_custom_phases_and_last_step_is_shortened():
    assert TimeSchedule(START, 26, phases=((24, 1.0), (float("inf"), 3.0))).elapsed_hours()[-2:] == [24, 26]
    assert TimeSchedule(START, 2.6).times()[-1] == datetime(2026, 11, 1, 14, 38, tzinfo=UTC)
