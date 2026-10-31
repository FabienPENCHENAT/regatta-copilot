"""Build the nautical-chart basemap layers used by the frontend map.

Downloads Natural Earth 1:10m land and bathymetry (public domain), clips them to the Atlantic race area,
simplifies them and writes compact GeoJSON files to frontend/map-data/.

Usage: python scripts/build_basemap.py   (needs shapely; downloads ~50 MB once into var/natural-earth/)
"""

import json
import urllib.request
from pathlib import Path

from shapely.geometry import box, mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "var" / "natural-earth"
OUTPUT_DIR = ROOT / "frontend" / "map-data"
SOURCE_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/{name}.geojson"

AREA = box(-85.0, 0.0, 15.0, 62.0)  # lon/lat bounds of every race we plan to support for now
LAND_TOLERANCE_DEG = 0.004  # ~400 m: keeps capes and islands readable at zoom 9
DEPTH_TOLERANCE_DEG = 0.03
DEPTH_LAYERS = {  # Natural Earth file -> depth in metres
    "ne_10m_bathymetry_K_200": 200,
    "ne_10m_bathymetry_J_1000": 1000,
    "ne_10m_bathymetry_I_2000": 2000,
    "ne_10m_bathymetry_H_3000": 3000,
    "ne_10m_bathymetry_G_4000": 4000,
    "ne_10m_bathymetry_F_5000": 5000,
}


def download(name: str) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{name}.geojson"
    if not path.exists():
        urllib.request.urlretrieve(SOURCE_URL.format(name=name), path)
    return json.loads(path.read_text())


def clipped_union(collection: dict, tolerance: float):
    shapes = [shape(f["geometry"]).buffer(0) for f in collection["features"]]
    return unary_union(shapes).intersection(AREA).simplify(tolerance, preserve_topology=True)


def rounded(value):
    if isinstance(value, float):
        return round(value, 3)
    if isinstance(value, (list, tuple)):
        return [rounded(v) for v in value]
    if isinstance(value, dict):
        return {k: rounded(v) for k, v in value.items()}
    return value


def write(name: str, features: list[dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{name}.geojson"
    path.write_text(json.dumps({"type": "FeatureCollection", "features": rounded(features)}, separators=(",", ":")))
    print(f"{path.relative_to(ROOT)}: {path.stat().st_size // 1024} KB")


def build_land() -> None:
    land = unary_union([
        clipped_union(download("ne_10m_land"), LAND_TOLERANCE_DEG),
        clipped_union(download("ne_10m_minor_islands"), LAND_TOLERANCE_DEG),
    ])
    write("land", [{"type": "Feature", "properties": {}, "geometry": mapping(land)}])


def build_depths() -> None:
    features = []
    for name, depth_m in DEPTH_LAYERS.items():
        area = clipped_union(download(name), DEPTH_TOLERANCE_DEG)
        features.append({"type": "Feature", "properties": {"depth_m": depth_m}, "geometry": mapping(area)})
    write("depths", features)


if __name__ == "__main__":
    build_land()
    build_depths()
