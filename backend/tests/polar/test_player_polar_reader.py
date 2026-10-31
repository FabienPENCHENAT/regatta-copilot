import copy
import json
from pathlib import Path

import pytest

from sailrouter.polar.player_polar_reader import InvalidPolarError, PlayerPolarReader

CLASS40 = Path(__file__).resolve().parents[3] / "data" / "polars" / "class40-2021.vr.json"


@pytest.fixture(scope="module")
def polar() -> dict:
    return json.loads(CLASS40.read_text(encoding="utf-8"))


def test_raw_polar_is_returned_as_is(polar):
    assert PlayerPolarReader().read(polar) == polar


def test_polar_nested_in_a_game_response_is_found_and_the_wrapper_dropped(polar):
    wrapper = {"@class": "LogEventResponse", "requestId": "abc", "userId": "secret-session",
               "scriptData": {"rc": "ok", "extendsData": {"boatPolar": polar}}}
    assert PlayerPolarReader().read(wrapper) == polar


def test_polar_inside_a_list_or_a_json_string_is_found(polar):
    assert PlayerPolarReader().read([{"other": 1}, {"res": {"polar": polar}}]) == polar
    assert PlayerPolarReader().read({"body": json.dumps(polar)}) == polar


@pytest.mark.parametrize("payload, message", [
    ({"hello": "world"}, "no VR polar found"),
    ("not json at all", "no VR polar found"),
])
def test_payload_without_polar_is_refused(payload, message):
    with pytest.raises(InvalidPolarError, match=message):
        PlayerPolarReader().read(payload)


def test_missing_sail_winch_or_broken_table_is_refused(polar):
    six_sails = copy.deepcopy(polar)
    six_sails["sail"].pop()
    no_winch = {k: v for k, v in polar.items() if k != "winch"}
    ragged = copy.deepcopy(polar)
    ragged["sail"][0]["speed"][3] = ragged["sail"][0]["speed"][3][:-1]
    no_foil = {k: v for k, v in polar.items() if k != "foil"}
    with pytest.raises(InvalidPolarError, match="7 sails"):
        PlayerPolarReader().read(six_sails)
    with pytest.raises(InvalidPolarError, match="winch"):
        PlayerPolarReader().read(no_winch)
    with pytest.raises(InvalidPolarError, match="not consistent"):
        PlayerPolarReader().read(ragged)
    with pytest.raises(InvalidPolarError, match="foil"):
        PlayerPolarReader().read(no_foil)
