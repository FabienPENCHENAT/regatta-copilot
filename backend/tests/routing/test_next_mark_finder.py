from dataclasses import replace
from pathlib import Path

from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.mark import Mark
from sailrouter.routing.next_mark_finder import NextMarkFinder

RACES = Path(__file__).resolve().parents[3] / "races"


def race():
    return RaceCatalog(RACES).load("route-du-rhum-2026")


def race_with_a_gate():
    """The real course plus a westward gate off Cap Fréhel first (as in the real race's instructions)."""
    gate = Mark(id="gate", kind="gate", cross="westward",
                points=(GeoPoint(48.696667, -2.308333), GeoPoint(48.713333, -2.308333)))
    rhum = race()
    return replace(rhum, marks=(gate, *rhum.marks))


def test_at_the_start_guadeloupe_is_the_first_mark():
    assert NextMarkFinder().first_ahead(race(), GeoPoint(48.718, -2.144)) == "tete_anglais"


def test_a_gate_ahead_stays_ahead_until_passed_by_the_margin():
    assert NextMarkFinder().first_ahead(race_with_a_gate(), GeoPoint(48.718, -2.144)) == "gate"
    assert NextMarkFinder().first_ahead(race_with_a_gate(), GeoPoint(48.705, -2.33)) == "gate"  # < 2 nm beyond
    assert NextMarkFinder().first_ahead(race_with_a_gate(), GeoPoint(48.705, -2.40)) == "tete_anglais"


def test_mid_atlantic_the_gate_is_passed_and_guadeloupe_marks_are_ahead():
    assert NextMarkFinder().first_ahead(race(), GeoPoint(45.0, -12.0)) == "tete_anglais"


def test_rounding_marks_are_never_passed_automatically():
    # far south of Tête à l'Anglais and east of the Les Saintes line: a position alone cannot tell they were rounded
    assert NextMarkFinder().first_ahead(race(), GeoPoint(16.0, -61.3)) == "tete_anglais"
    assert NextMarkFinder().first_ahead(race(), GeoPoint(17.0, -60.0)) == "tete_anglais"
