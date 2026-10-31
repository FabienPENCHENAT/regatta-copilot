from pathlib import Path

from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.routing.next_mark_finder import NextMarkFinder

RACES = Path(__file__).resolve().parents[3] / "races"


def race():
    return RaceCatalog(RACES).load("route-du-rhum-2026")


def test_at_the_start_the_frehel_gate_is_ahead():
    assert NextMarkFinder().first_ahead(race(), GeoPoint(48.73, -1.9)) == "frehel_gate"


def test_just_past_the_gate_by_less_than_the_margin_it_is_still_ahead():
    assert NextMarkFinder().first_ahead(race(), GeoPoint(48.705, -2.33)) == "frehel_gate"


def test_mid_atlantic_the_gate_is_passed_and_guadeloupe_marks_are_ahead():
    assert NextMarkFinder().first_ahead(race(), GeoPoint(45.0, -12.0)) == "tete_anglais"
