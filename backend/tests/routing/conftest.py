"""Small synthetic world for routing tests: constant wind, a one-sail polar with a known answer, no land."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

from sailrouter.geography.coastline_loader import CoastlineLoader
from sailrouter.geography.land_mask import LandMask
from sailrouter.geography.obstacle_checker import ObstacleChecker
from sailrouter.geography.polygon_rasterizer import PolygonRasterizer
from sailrouter.geography.raster_grid import RasterGrid
from sailrouter.geography.zone_crossing_detector import ZoneCrossingDetector
from sailrouter.polar.boat_options import BoatOptions
from sailrouter.polar.boat_polar import BoatPolar
from sailrouter.polar.foil_bonus import FoilBonus
from sailrouter.polar.maneuver_penalty import ManeuverPenalty
from sailrouter.polar.speed_model import SpeedModel
from sailrouter.polar.vr_polar import VrPolar
from sailrouter.polar.winch_timings import MANEUVERS, ManeuverTiming, WinchTimings
from sailrouter.routing.heading_fan import HeadingFan
from sailrouter.routing.isochrone_pruner import IsochronePruner
from sailrouter.routing.isochrone_router import IsochroneRouter
from sailrouter.weather.wind_field import WindField
from sailrouter.weather.wind_grid import WindGrid

T0 = datetime(2026, 11, 1, 12, tzinfo=UTC)
ISLAND = Path(__file__).resolve().parents[1] / "fixtures" / "island.geojson"
BOAT_SPEED_KN = 10.0


def constant_wind_from_north(speed_ms: float = 10.0) -> WindField:
    lat, lon = np.arange(40.0, 60.25, 0.25), np.arange(-20.0, 0.25, 0.25)
    u = np.zeros((lat.size, lon.size), np.float32)
    v = np.full_like(u, -speed_ms)  # blowing southward = wind from 0°
    return WindField([WindGrid(T0 + timedelta(hours=h), lat, lon, u, v) for h in (0, 240)])


def one_sail_speed_model() -> SpeedModel:
    """10 kn at any TWA from 45° to 180°, nothing closer to the wind: best upwind VMG is 10·cos 45°."""
    speeds = [[[0, 0], [0, 0], [BOAT_SPEED_KN] * 2, [BOAT_SPEED_KN] * 2]]
    polar = BoatPolar([0, 40], [0, 44, 45, 180], ("Jib",), speeds)
    vr = VrPolar("test", polar, FoilBonus(1.0, 80, 160, 10, 16, 35, 5), 1.0, 1.0, zero_winch())
    return SpeedModel(vr, BoatOptions(foil=False, hull=False))


def zero_winch() -> WinchTimings:
    timing = ManeuverTiming(0, 1, 0, 1)
    return WinchTimings({(m, level): timing for m in MANEUVERS for level in ("std", "pro")}, 10, 30)


def obstacles(with_island: bool) -> ObstacleChecker:
    grid = RasterGrid(40.0, -20.0, 60.0, 0.0, 0.01)
    polygons = CoastlineLoader().load(ISLAND) if with_island else []
    return ObstacleChecker(LandMask(grid, PolygonRasterizer(grid).rasterize(polygons)), ZoneCrossingDetector([]))


@pytest.fixture
def make_router():
    def build(with_island: bool = False, tack_loss_s: float = 0.0) -> IsochroneRouter:
        speed = one_sail_speed_model()
        penalty = ManeuverPenalty(zero_winch(), fixed_loss_s={"tack": tack_loss_s, "gybe": 0, "sailChange": 0})
        return IsochroneRouter(
            constant_wind_from_north(), speed, penalty, obstacles(with_island), HeadingFan(5.0, 360.0), IsochronePruner(0.5)
        )

    return build
