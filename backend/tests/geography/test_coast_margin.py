import numpy as np

from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.mark import Mark
from sailrouter.geography.coast_margin import CoastMargin
from sailrouter.geography.gate_corridors import GateCorridors
from sailrouter.geography.land_mask import LandMask
from sailrouter.geography.obstacle_checker import ObstacleChecker
from sailrouter.geography.raster_grid import RasterGrid
from sailrouter.geography.zone_crossing_detector import ZoneCrossingDetector

GRID = RasterGrid(0.0, 0.0, 1.0, 1.0, 0.005)  # 200 × 200 cells at the equator


def _island():
    mask = np.zeros((GRID.n_rows, GRID.n_cols), dtype=bool)
    mask[95:105, 95:105] = True  # 0.05° square around (0.5, 0.5)
    return np.packbits(mask, axis=1)


def test_the_margin_grows_land_by_about_one_mile():
    widened = LandMask(GRID, CoastMargin(1.0).widen(GRID, _island()))
    edge = 0.525  # east edge of the island
    assert widened.is_land([0.5], [edge + 0.95 / 60])[0]  # 0.95 nm off: inside the margin
    assert not widened.is_land([0.5], [edge + 1.3 / 60])[0]  # 1.3 nm off: open water
    corner = edge + 0.85 / 60  # 0.85 nm north and east of the island's corner: 1.2 nm away
    assert not widened.is_land([corner], [corner])[0]  # rounded corners (ellipse, not a square)


def test_a_gate_reopens_the_margin_around_it_but_not_the_land():
    land = _island()
    gate = Mark(id="gate", kind="gate", points=(GeoPoint(0.5, 0.53), GeoPoint(0.5, 0.56)), cross="northward")
    margin = GateCorridors(1.0).open(GRID, CoastMargin(1.0).widen(GRID, land), land, [gate])
    mask = LandMask(GRID, margin)
    assert not mask.is_land([0.5], [0.535])[0] and mask.is_land([0.5], [0.5])[0]
    assert mask.is_land([0.47], [0.5])[0]  # far side of the island, away from the gate: margin kept


def test_a_boat_cannot_enter_the_margin_but_can_leave_it():
    land = LandMask(GRID, _island())
    checker = ObstacleChecker(land, ZoneCrossingDetector(()), LandMask(GRID, CoastMargin(1.0).widen(GRID, _island())))
    inside, outside, closer = (0.5, 0.535), (0.5, 0.56), (0.5, 0.53)
    assert checker.blocked([outside[0]], [outside[1]], [inside[0]], [inside[1]])[0]  # entering
    assert not checker.blocked([inside[0]], [inside[1]], [outside[0]], [outside[1]])[0]  # leaving
    assert not checker.blocked([inside[0]], [inside[1]], [closer[0]], [closer[1]])[0]  # inside: only land counts
    assert checker.blocked([inside[0]], [inside[1]], [0.5], [0.5])[0]  # into real land
