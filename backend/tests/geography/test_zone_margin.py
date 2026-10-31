import numpy as np

from sailrouter.domain.exclusion_zone import ExclusionZone
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.mark import Mark
from sailrouter.geography.zone_crossing_detector import ZoneCrossingDetector
from sailrouter.geography.zone_margin import ZoneMargin

SQUARE = ExclusionZone("farm", "polygon", (GeoPoint(45.0, -5.0), GeoPoint(45.0, -4.9), GeoPoint(45.1, -4.9),
                                           GeoPoint(45.1, -5.0)))


def _blocked(zones, lat0, lon0, lat1, lon1):
    return bool(ZoneCrossingDetector(zones).blocked(*(np.array([v], float) for v in (lat0, lon0, lat1, lon1)))[0])


def test_a_zone_grows_by_about_one_mile():
    [wide] = ZoneMargin(1.0).widen([SQUARE], [])
    assert wide.shape == "polygon"
    north_edge = 45.1
    assert _blocked([wide], north_edge + 0.9 / 60, -4.95, north_edge + 0.9 / 60, -4.95)  # 0.9 nm off: in the margin
    assert not _blocked([wide], north_edge + 1.2 / 60, -4.95, north_edge + 1.2 / 60, -4.95)  # 1.2 nm off: clear


def test_a_forbidden_line_becomes_a_corridor():
    line = ExclusionZone("rail", "line", (GeoPoint(45.0, -5.0), GeoPoint(45.0, -4.8)))
    [corridor] = ZoneMargin(1.0).widen([line], [])
    assert corridor.shape == "polygon"
    assert _blocked([corridor], 45.0 + 3 / 60, -4.9, 45.0 + 0.5 / 60, -4.9)  # from 3 nm north to 0.5 nm off
    assert not _blocked([corridor], 45.0 + 3 / 60, -4.9, 45.0 + 1.5 / 60, -4.9)  # stops 1.5 nm off


def test_a_zone_touching_a_gate_keeps_its_own_shape():
    gate = Mark(id="finish", kind="line", cross="northward",
                points=(GeoPoint(45.11, -4.95), GeoPoint(45.11, -4.94)))  # 0.6 nm north of the zone
    [kept] = ZoneMargin(1.0).widen([SQUARE], [gate])
    assert kept is SQUARE
