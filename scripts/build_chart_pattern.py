"""Build the decorative nautical-chart pattern used behind the page.

One seamless tile in the style of a sea chart / portolan: rhumb lines radiating from compass roses (drawn from
the rose and its periodic neighbours so lines continue across tile edges), dashed isobaths of a smooth periodic
sea floor, and scattered depth soundings in italic. The SVG is used as a CSS mask, so its colour comes from the
page theme.

Usage: python scripts/build_chart_pattern.py   (needs numpy and matplotlib)
"""

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "frontend" / "styles" / "chart-pattern.svg"
TILE = 900
ROSES = [(270.0, 300.0), (720.0, 690.0)]  # rose centres inside the tile
RHUMB_COUNT = 16
ISOBATH_LEVELS = 7
SOUNDINGS = 42
SEED = 11


def rhumb_lines() -> str:
    """Lines from every rose and its 8 periodic neighbours, clipped by the tile viewBox."""
    paths = []
    for cx, cy in ROSES:
        for dx in (-TILE, 0, TILE):
            for dy in (-TILE, 0, TILE):
                ox, oy = cx + dx, cy + dy
                for k in range(RHUMB_COUNT):
                    angle = 2 * math.pi * k / RHUMB_COUNT
                    ex, ey = ox + 2 * TILE * math.cos(angle), oy + 2 * TILE * math.sin(angle)
                    paths.append(f"M{ox:.0f} {oy:.0f}L{ex:.0f} {ey:.0f}")
    return f'<path d="{"".join(paths)}" stroke-width="0.6" opacity="0.55"/>'


def compass_rose(cx: float, cy: float, radius: float = 62) -> str:
    points = []
    for k in range(16):
        angle = 2 * math.pi * k / 16 - math.pi / 2
        length = radius if k % 4 == 0 else radius * 0.62 if k % 2 == 0 else radius * 0.4
        tip = (cx + length * math.cos(angle), cy + length * math.sin(angle))
        side = 2 * math.pi / 64
        left = (cx + radius * 0.11 * math.cos(angle - side * 4), cy + radius * 0.11 * math.sin(angle - side * 4))
        right = (cx + radius * 0.11 * math.cos(angle + side * 4), cy + radius * 0.11 * math.sin(angle + side * 4))
        points.append(f"M{cx:.1f} {cy:.1f}L{left[0]:.1f} {left[1]:.1f}L{tip[0]:.1f} {tip[1]:.1f}L{right[0]:.1f} {right[1]:.1f}Z")
    rings = (f'<circle cx="{cx}" cy="{cy}" r="{radius * 1.12:.0f}" fill="none" stroke-width="1.4"/>'
             f'<circle cx="{cx}" cy="{cy}" r="{radius * 1.2:.0f}" fill="none" stroke-width="0.6" stroke-dasharray="2 4"/>')
    return f'{rings}<path d="{"".join(points)}" fill="#000" fill-opacity="0.35" stroke-width="0.8"/>'


def periodic_floor(size: int, rng: np.random.Generator) -> np.ndarray:
    t = np.linspace(0, 2 * np.pi, size, endpoint=False)
    x, y = np.meshgrid(t, t)
    floor = np.zeros_like(x)
    for _ in range(10):
        kx, ky = rng.integers(-2, 3, size=2)
        if kx == 0 and ky == 0:
            continue
        floor += np.sin(kx * x + ky * y + rng.uniform(0, 2 * np.pi)) / np.hypot(kx, ky) ** 1.4
    return floor


def isobaths(floor: np.ndarray) -> str:
    wrapped = np.pad(floor, ((0, 1), (0, 1)), mode="wrap")
    coords = np.linspace(0, TILE, floor.shape[0] + 1)
    levels = np.linspace(floor.min(), floor.max(), ISOBATH_LEVELS + 2)[1:-1]
    contours = plt.contour(coords, coords, wrapped, levels=levels)
    paths = []
    for segments in contours.allsegs:
        for segment in segments:
            if len(segment) > 3:
                points = segment[:: max(1, len(segment) // 90)]
                paths.append("M" + "L".join(f"{x:.0f} {y:.0f}" for x, y in points))
    plt.close("all")
    return f'<path d="{"".join(paths)}" stroke-width="1.1" stroke-dasharray="7 4 1.5 4"/>'


def soundings(rng: np.random.Generator) -> str:
    texts, placed = [], []
    while len(texts) < SOUNDINGS:
        x, y = rng.uniform(20, TILE - 40, size=2)
        if any(math.hypot(x - cx, y - cy) < 95 for cx, cy in ROSES):
            continue
        if any(math.hypot(x - px, y - py) < 70 for px, py in placed):
            continue
        placed.append((x, y))
        depth = int(rng.choice([rng.integers(8, 60), rng.integers(60, 400), rng.integers(1000, 4800)]))
        texts.append(f'<text x="{x:.0f}" y="{y:.0f}">{depth}</text>')
    return (f'<g stroke="none" fill="#000" font-family="Georgia, serif" font-style="italic" font-size="13">'
            f'{"".join(texts)}</g>')


if __name__ == "__main__":
    rng = np.random.default_rng(SEED)
    body = rhumb_lines() + isobaths(periodic_floor(240, rng)) + soundings(rng)
    body += "".join(compass_rose(cx, cy) for cx, cy in ROSES)
    OUTPUT.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{TILE}" height="{TILE}" viewBox="0 0 {TILE} {TILE}">'
        f'<g fill="none" stroke="#000" stroke-linecap="round">{body}</g></svg>'
    )
    print(f"{OUTPUT.relative_to(ROOT)}: {OUTPUT.stat().st_size // 1024} KB")
