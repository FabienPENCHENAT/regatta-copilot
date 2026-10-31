import pytest

from sailrouter.polar.boat_options import BoatOptions

ALL_SAILS = ("Jib", "Spi", "LightJib", "LightGnk", "Staysail", "HeavyGnk", "Code0")


def allowed(options):
    return [sail for sail in ALL_SAILS if options.allows_sail(sail)]


def test_all_is_the_full_pack():
    assert BoatOptions.from_owned("all") == BoatOptions()


def test_foil_only_keeps_jib_and_spi():
    options = BoatOptions.from_owned("foil")
    assert options.foil and not options.hull and not options.pro_winch
    assert allowed(options) == ["Jib", "Spi"]


def test_sails_can_be_owned_one_by_one():
    options = BoatOptions.from_owned("LightGnk,Code0,foil")
    assert allowed(options) == ["Jib", "Spi", "LightGnk", "Code0"]


def test_pack_shorthand_adds_both_sails():
    assert allowed(BoatOptions.from_owned("light")) == ["Jib", "Spi", "LightJib", "LightGnk"]


def test_none_is_the_bare_boat():
    options = BoatOptions.from_owned("none")
    assert allowed(options) == ["Jib", "Spi"] and not (options.foil or options.hull or options.pro_winch)


def test_unknown_option_is_refused():
    with pytest.raises(ValueError, match="magic"):
        BoatOptions.from_owned("foil,magic")
