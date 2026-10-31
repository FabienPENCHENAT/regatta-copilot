from pathlib import Path

import numpy as np
import pytest

from sailrouter.domain.exclusion_zone import ExclusionZone
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.geography.coastline_loader import CoastlineLoader
from sailrouter.geography.land_mask import LandMask
from sailrouter.geography.obstacle_checker import ObstacleChecker
from sailrouter.geography.polygon_rasterizer import PolygonRasterizer
from sailrouter.geography.raster_grid import RasterGrid
from sailrouter.geography.zone_crossing_detector import ZoneCrossingDetector

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "backend" / "tests" / "fixtures" / "island.geojson"


def checker(source: Path, grid: RasterGrid, zones=()) -> ObstacleChecker:
    land = LandMask(grid, PolygonRasterizer(grid).rasterize(CoastlineLoader().load(source)))
    return ObstacleChecker(land, ZoneCrossingDetector(zones))


def segments(*rows):
    return [np.array(column, float) for column in zip(*rows)]  # lat0, lon0, lat1, lon1


def test_segment_through_the_island_is_blocked():
    grid = RasterGrid(47.5, -4.0, 48.5, -2.0, 0.005)
    check = checker(FIXTURE, grid)
    blocked = check.blocked(*segments(
        (48.1, -3.5, 48.1, -2.8),    # straight through the island
        (48.25, -3.5, 48.25, -2.8),  # north of it
        (48.1, -3.5, 48.05, -3.15),  # ends on the island
        (48.1, -3.5, 48.1, -4.5),    # leaves the raster area
    ))
    assert blocked.tolist() == [True, False, True, True]


def test_polygon_and_line_zones():
    square = ExclusionZone("tss", "polygon", tuple(GeoPoint(*p) for p in [(47.6, -3.9), (47.6, -3.7), (47.8, -3.7), (47.8, -3.9)]))
    fence = ExclusionZone("fence", "line", (GeoPoint(47.6, -3.4), GeoPoint(47.8, -3.4)))
    check = checker(FIXTURE, RasterGrid(47.5, -4.0, 48.5, -2.0, 0.005), [square, fence])
    blocked = check.blocked(*segments(
        (47.7, -3.95, 47.7, -3.65),  # through the square
        (47.7, -3.8, 47.7, -3.6),    # starts inside: leaving is allowed
        (47.7, -3.5, 47.7, -3.3),    # crosses the fence
        (47.9, -3.5, 47.9, -3.3),    # passes north of the fence
    ))
    assert blocked.tolist() == [True, False, True, False]


@pytest.fixture(scope="module")
def brittany():
    # Real coastline, raster restricted to the start area to keep the test fast.
    return checker(ROOT / "frontend" / "map-data" / "land.geojson", RasterGrid(48.0, -3.5, 49.5, -1.0, 0.005))


def test_frehel_gate_stays_open_and_the_cape_is_land(brittany):
    gate_lon = -2.308333
    lat = np.linspace(48.702, 48.712, 5)
    blocked = brittany.blocked(lat, np.full(5, gate_lon + 0.05), lat, np.full(5, gate_lon - 0.05))
    assert not blocked.any()
    assert brittany.blocked([48.75], [-2.30], [48.62], [-2.33])[0]  # across Cap Fréhel
