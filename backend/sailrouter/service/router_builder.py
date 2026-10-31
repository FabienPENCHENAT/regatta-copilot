from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from sailrouter.domain.race import Race
from sailrouter.geography.coast_margin import CoastMargin
from sailrouter.geography.coastline_loader import CoastlineLoader
from sailrouter.geography.gate_corridors import GateCorridors
from sailrouter.geography.land_mask import LandMask
from sailrouter.geography.obstacle_checker import ObstacleChecker
from sailrouter.geography.polygon_rasterizer import PolygonRasterizer
from sailrouter.geography.raster_grid import RasterGrid
from sailrouter.geography.zone_crossing_detector import ZoneCrossingDetector
from sailrouter.polar.boat_options import BoatOptions
from sailrouter.polar.maneuver_penalty import ManeuverPenalty
from sailrouter.polar.speed_model import SpeedModel
from sailrouter.polar.vr_polar_parser import VrPolarParser
from sailrouter.polar.winch_timings import ManeuverTiming
from sailrouter.routing.heading_fan import HeadingFan
from sailrouter.routing.isochrone_pruner import IsochronePruner
from sailrouter.routing.isochrone_router import IsochroneRouter
from sailrouter.service.project_paths import ProjectPaths
from sailrouter.weather.weather_area import WeatherArea
from sailrouter.weather.wind_field import WindField

WEATHER_AREA = WeatherArea(south_deg=0.0, north_deg=60.0, west_deg=-80.0, east_deg=10.0)
LAND_RESOLUTION_DEG = 0.005  # ≈ 550 m × 370 m at 48°N: keeps the 1 nm wide Fréhel gate open
COAST_MARGIN_NM = 1.0  # routes keep this far from Natural Earth's coast, which differs from the game's (D46)


class RouterBuilder:
    """Builds the weather-independent parts of a routing run (boat models, land and zones) and the isochrone
    router for a wind field. Shared by the GFS planner and the GEFS member workers."""

    def __init__(self, paths: ProjectPaths) -> None:
        self._paths = paths

    def boat_models(
        self, polar_file: Path, options: BoatOptions, maneuvers: dict[str, ManeuverTiming],
    ) -> tuple[SpeedModel, ManeuverPenalty]:
        vr_polar = VrPolarParser().load(polar_file)
        winch = vr_polar.winch.with_overrides("pro" if options.pro_winch else "std", maneuvers)
        return SpeedModel(vr_polar, options), ManeuverPenalty(winch, pro_winch=options.pro_winch)

    def obstacles(self, race: Race) -> ObstacleChecker:
        area = WEATHER_AREA
        grid = RasterGrid(area.south_deg, area.west_deg, area.north_deg, area.east_deg, LAND_RESOLUTION_DEG)
        packed = PolygonRasterizer(grid).rasterize(CoastlineLoader().load(self._paths.land_geojson))
        widened = GateCorridors(COAST_MARGIN_NM).open(grid, self._widened_land(grid, packed), packed,
                                                      [*race.marks, race.finish])
        margin = LandMask(grid, widened)
        return ObstacleChecker(LandMask(grid, packed), ZoneCrossingDetector(race.exclusion_zones), margin)

    def _widened_land(self, grid: RasterGrid, packed: np.ndarray) -> np.ndarray:
        """The land raster widened by the coast margin, kept on disk (a few seconds to build, then shared by the
        member workers). The file name holds everything it depends on."""
        source = self._paths.land_geojson.stat()
        name = f"coast-{COAST_MARGIN_NM:g}nm-{LAND_RESOLUTION_DEG:g}deg-{source.st_size}-{int(source.st_mtime)}.npy"
        path = self._paths.land_cache_dir / name
        if path.exists():
            return np.load(path)
        widened = CoastMargin(COAST_MARGIN_NM).widen(grid, packed)
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_suffix(f".{os.getpid()}.partial.npy")
        np.save(partial, widened)
        os.replace(partial, path)
        return widened

    @staticmethod
    def router(
        wind: WindField, speed_model: SpeedModel, penalty: ManeuverPenalty, obstacles: ObstacleChecker,
    ) -> IsochroneRouter:
        return IsochroneRouter(wind, speed_model, penalty, obstacles, HeadingFan(1.0, 220.0), IsochronePruner(0.5))
