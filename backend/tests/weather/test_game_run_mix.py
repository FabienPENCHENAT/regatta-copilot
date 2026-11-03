from datetime import UTC, datetime, timedelta

from sailrouter.weather.game_run_mix import GameRunMix
from sailrouter.weather.lead_time_plan import LeadTimePlan
from sailrouter.weather.model_run import ModelRun

RUN_06Z = ModelRun("gfs", datetime(2026, 11, 3, 6, tzinfo=UTC))
RUN_00Z = ModelRun("gfs", datetime(2026, 11, 3, 0, tzinfo=UTC))


def test_the_first_hours_keep_the_previous_run_like_the_game():
    start = datetime(2026, 11, 3, 12, 18, tzinfo=UTC)  # game logbook: 00Z current, 06Z next
    steps = GameRunMix(LeadTimePlan.game()).steps(RUN_06Z, start, start + timedelta(hours=7))
    assert steps == [(RUN_00Z, 12), (RUN_06Z, 9), (RUN_06Z, 12), (RUN_06Z, 15)]


def test_once_past_nine_hours_everything_comes_from_the_newest_run():
    start = datetime(2026, 11, 3, 15, 30, tzinfo=UTC)
    steps = GameRunMix(LeadTimePlan.game()).steps(RUN_06Z, start, start + timedelta(hours=2))
    assert steps == [(RUN_06Z, 9), (RUN_06Z, 12)]
