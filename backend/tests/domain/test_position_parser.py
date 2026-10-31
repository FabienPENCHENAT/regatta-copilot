import pytest

from sailrouter.domain.position_parser import PositionParser

parser = PositionParser()


@pytest.mark.parametrize(
    ("text", "lat", "lon"),
    [
        ("46°12'30\"N 012°34'10\"W", 46 + 12 / 60 + 30 / 3600, -(12 + 34 / 60 + 10 / 3600)),
        ("46°12.5'N 12°34.2'W", 46 + 12.5 / 60, -(12 + 34.2 / 60)),
        ("46.21, -12.57", 46.21, -12.57),
        ("46,21 ; -12,57", 46.21, -12.57),
        ("46.21N 12.57W", 46.21, -12.57),
        ("46.21N 12.57O", 46.21, -12.57),
        ("46.21n 12.57e", 46.21, 12.57),
        ("12°34'10\"S 046°12'30\"E", -(12 + 34 / 60 + 10 / 3600), 46 + 12 / 60 + 30 / 3600),
        ("48°43'48''N 001°54'00''W", 48.73, -1.9),
        ("48°43′48″N 001°54′00″W", 48.73, -1.9),
        ("  47.5 -6.75  ", 47.5, -6.75),
        ("12°34'W 46°12'N", 46.2, -(12 + 34 / 60)),
    ],
)
def test_parses_accepted_formats(text, lat, lon):
    point = parser.parse(text)
    assert point is not None
    assert point.lat_deg == pytest.approx(lat, abs=1e-9)
    assert point.lon_deg == pytest.approx(lon, abs=1e-9)


@pytest.mark.parametrize(
    "text",
    ["", "   ", None, "hello", "46.21N", "46.21N 12.57N", "95, 10", "45, 190", "46.21N 12.57W 3.0E"],
)
def test_rejects_unknown_or_invalid_text(text):
    assert parser.parse(text) is None
