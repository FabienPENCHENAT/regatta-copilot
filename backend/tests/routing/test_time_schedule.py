from datetime import UTC, datetime

from sailrouter.routing.time_schedule import TimeSchedule

START = datetime(2026, 11, 1, 12, 2, tzinfo=UTC)


def test_hourly_then_three_hourly():
    hours = TimeSchedule(START, 120).elapsed_hours()
    assert hours[:3] == [0, 1, 2]
    assert hours[24:27] == [24, 27, 30]
    assert hours[-1] == 120
    assert len(hours) - 1 == 24 + 32
    assert {4, 8, 12, 16, 24, 48} <= set(hours)


def test_last_step_is_shortened():
    assert TimeSchedule(START, 26).elapsed_hours()[-2:] == [24, 26]
    assert TimeSchedule(START, 2.5).times()[-1] == datetime(2026, 11, 1, 14, 32, tzinfo=UTC)
