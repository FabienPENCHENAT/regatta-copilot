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


def test_rounding_marks_are_never_passed_automatically():
    # far south of Tête à l'Anglais and east of the Les Saintes line: a position alone cannot tell they were rounded
    assert NextMarkFinder().first_ahead(race(), GeoPoint(16.0, -61.3)) == "tete_anglais"
    assert NextMarkFinder().first_ahead(race(), GeoPoint(17.0, -60.0)) == "tete_anglais"
