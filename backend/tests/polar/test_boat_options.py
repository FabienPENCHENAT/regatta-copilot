import pytest

from sailrouter.polar.boat_options import BoatOptions


def test_all_is_the_full_pack():
    assert BoatOptions.from_owned("all") == BoatOptions()


def test_foil_only_keeps_jib_and_spi():
    options = BoatOptions.from_owned("foil")
    assert options.foil and not options.hull and not options.pro_winch
    assert [s for s in ("Jib", "Spi", "LightJib", "LightGnk", "Staysail", "HeavyGnk", "Code0") if options.allows_sail(s)] == [
        "Jib",
        "Spi",
    ]


def test_none_is_the_bare_boat():
    options = BoatOptions.from_owned("none")
    assert not any((options.light, options.heavy, options.reach, options.foil, options.hull, options.pro_winch))


def test_unknown_option_is_refused():
    with pytest.raises(ValueError, match="magic"):
        BoatOptions.from_owned("foil,magic")
