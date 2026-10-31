import numpy as np
import pytest

from sailrouter.polar.maneuver_penalty import ManeuverPenalty
from sailrouter.polar.winch_timings import MANEUVERS, ManeuverTiming, WinchTimings


def winch() -> WinchTimings:
    timings = {}
    for maneuver in MANEUVERS:
        timings[(maneuver, "pro")] = ManeuverTiming(180, 0.7, 300, 0.7)
        timings[(maneuver, "std")] = ManeuverTiming(180, 0.5, 300, 0.5)
    timings[("sailChange", "pro")] = ManeuverTiming(240, 0.7, 360, 0.7)
    return WinchTimings(timings, light_wind_kn=10, heavy_wind_kn=30)


def test_loss_interpolates_between_light_and_heavy_wind():
    penalty = ManeuverPenalty(winch(), pro_winch=True)
    assert penalty.loss_for("tack", [5, 10, 20, 40]) == pytest.approx([54, 54, 72, 90])
    assert ManeuverPenalty(winch(), pro_winch=False).loss_for("gybe", 10) == pytest.approx(90)


def test_detects_tack_gybe_and_sail_change():
    penalty = ManeuverPenalty(winch(), fixed_loss_s={"tack": 60, "gybe": 100, "sailChange": 30})
    previous_twa = np.array([45, 150, 45, 45, np.nan, -45])
    new_twa = np.array([-45, -150, 50, 50, -45, -40])
    previous_sail = np.array([0, 0, 0, 0, -1, 1])
    new_sail = np.array([0, 0, 0, 1, 0, 2])
    loss = penalty.loss_s(previous_twa, previous_sail, new_twa, new_sail, 15.0)
    # tack, gybe, nothing, sail change, start (unknown state), sail change only
    assert loss == pytest.approx([60, 100, 0, 30, 0, 30])


def test_tack_with_sail_change_costs_the_larger():
    penalty = ManeuverPenalty(winch(), fixed_loss_s={"tack": 60, "sailChange": 80})
    assert penalty.loss_s(40, 0, -40, 1, 15.0) == pytest.approx(80)
