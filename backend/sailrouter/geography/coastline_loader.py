from __future__ import annotations

import json
from pathlib import Path

import shapely
from shapely.geometry import Polygon, shape


class CoastlineLoader:
    """Reads a land GeoJSON (Natural Earth, `frontend/map-data/land.geojson`) into valid polygons.

    Coordinates rounded to 0.001° make a few polygons invalid for GEOS, so every geometry goes through
    `make_valid`. Polygons are oriented (exterior counter-clockwise, holes clockwise) for the rasterizer.
    """

    def load(self, path: Path) -> list[Polygon]:
        collection = json.loads(path.read_text(encoding="utf-8"))
        polygons: list[Polygon] = []
        for feature in collection["features"]:
            geometry = shapely.make_valid(shape(feature["geometry"]))
            for part in shapely.get_parts(geometry):
                polygons.extend(self._polygons_of(part))
        return [shapely.orient_polygons(polygon) for polygon in polygons]

    def _polygons_of(self, geometry) -> list[Polygon]:
        if isinstance(geometry, Polygon):
            return [] if geometry.is_empty else [geometry]
        if geometry.geom_type in ("MultiPolygon", "GeometryCollection"):
            return [p for part in shapely.get_parts(geometry) for p in self._polygons_of(part)]
        return []  # lines and points left over by make_valid have no area
