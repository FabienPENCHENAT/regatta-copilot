from pathlib import Path

import numpy as np
import pytest

from sailrouter.polar.boat_options import BoatOptions
from sailrouter.polar.speed_model import SpeedModel
from sailrouter.polar.vr_polar_parser import VrPolarParser

POLAR = Path(__file__).resolve().parents[3] / "data" / "polars" / "class40-2021.vr.json"


@pytest.fixture(scope="module")
def vr_polar():
    return VrPolarParser().load(POLAR)


def test_parses_the_class40_polar(vr_polar):
    assert vr_polar.label == "mono/class40-2021"
    assert vr_polar.polar.sail_names == ("Jib", "Spi", "Staysail", "LightJib", "Code0", "HeavyGnk", "LightGnk")
    assert vr_polar.polar.speeds_kn.shape == (7, 31, 16)
    assert vr_polar.hull_ratio == pytest.approx(1.003)
    assert vr_polar.winch.timing("tack", "pro").light_ratio == pytest.approx(0.7)


def test_table_values_and_bilinear_lookup(vr_polar):
    polar = vr_polar.polar
    jib = polar.sail_names.index("Jib")
    # Table node: TWA 90 (index 14), TWS 10 kn (index 4) → 9.71 kn for the Jib.
    assert polar.speeds(10.0, 90.0)[jib] == pytest.approx(9.71)
    # Halfway between TWS 10 (9.71) and 12 (10.42) at TWA 90.
    assert polar.speeds(11.0, 90.0)[jib] == pytest.approx((9.71 + 10.42) / 2)
    assert polar.speeds(np.array([10.0, 11.0]), 90.0).shape == (7, 2)


def test_best_sail_without_bonus(vr_polar):
    model = SpeedModel(vr_polar, BoatOptions(foil=False, hull=False))
    sail, speed = model.best(np.array([10.0]), np.array([-90.0]))  # signed TWA is accepted
    assert model.sail_names[sail[0]] == "Code0"  # 10.01 kn beats the Jib's 9.71 kn
    assert speed[0] == pytest.approx(10.01)


def test_options_restrict_sails_and_add_bonuses(vr_polar):
    no_reach = SpeedModel(vr_polar, BoatOptions(reach=False, foil=False, hull=False))
    sail, speed = no_reach.best(np.array([10.0]), np.array([90.0]))
    assert no_reach.sail_names[sail[0]] == "Jib" and speed[0] == pytest.approx(9.71)
    full = SpeedModel(vr_polar, BoatOptions())
    _, base = SpeedModel(vr_polar, BoatOptions(foil=False, hull=False)).best(20.0, 120.0)
    _, boosted = full.best(20.0, 120.0)  # inside the foil range: ×1.04 × hull 1.003
    assert boosted == pytest.approx(base * 1.04 * 1.003)
    _, edge = full.best(13.5, 120.0)  # TWS 13.5: halfway in the 11–16 kn foil ramp
    _, edge_base = SpeedModel(vr_polar, BoatOptions(foil=False)).best(13.5, 120.0)
    assert edge == pytest.approx(edge_base * 1.02)
