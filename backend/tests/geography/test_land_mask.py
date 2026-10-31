from pathlib import Path

import numpy as np

from sailrouter.geography.coastline_loader import CoastlineLoader
from sailrouter.geography.land_mask import LandMask
from sailrouter.geography.polygon_rasterizer import PolygonRasterizer
from sailrouter.geography.raster_grid import RasterGrid

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "island.geojson"
GRID = RasterGrid(south_deg=47.5, west_deg=-4.0, north_deg=48.5, east_deg=-2.0, resolution_deg=0.005)


def island_mask() -> LandMask:
    polygons = CoastlineLoader().load(FIXTURE)
    return LandMask(GRID, PolygonRasterizer(GRID).rasterize(polygons))


def test_island_lake_and_repaired_polygon():
    mask = island_mask()
    lat = np.array([48.05, 48.10, 48.30, 48.05, 48.18, 48.15])
    lon = np.array([-3.15, -3.10, -3.10, -2.58, -2.50, -2.42])
    # island, lake (water), open sea, left wing of the bow tie, gap above its crossing, right wing
    assert mask.is_land(lat, lon).tolist() == [True, False, False, True, False, True]


def test_outside_the_raster_counts_as_land():
    mask = island_mask()
    assert mask.is_land([10.0, 48.3], [-3.0, -5.0]).tolist() == [True, True]


def test_coarse_mask_is_conservative():
    mask = island_mask()
    rng = np.random.default_rng(1)
    lat = rng.uniform(47.6, 48.4, 20_000)
    lon = rng.uniform(-3.9, -2.1, 20_000)
    land = mask.is_land(lat, lon)
    assert mask.may_be_near_land(lat[land], lon[land]).all()
    assert not mask.may_be_near_land(47.7, -3.8)
