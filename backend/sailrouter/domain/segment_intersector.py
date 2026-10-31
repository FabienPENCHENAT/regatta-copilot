from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


class SegmentIntersector:
    """Planar segment–segment intersection test in (lon, lat) degrees, vectorised (arguments broadcast).

    Touching (an end on the other segment) counts as intersecting. Good enough for short segments and small
    race features (gates, lines, zones); not meant for ocean-scale segments.
    """

    @staticmethod
    def intersects(px, py, qx, qy, ax, ay, bx, by) -> NDArray[np.bool_]:
        """Whether segment P→Q intersects segment A→B."""
        d1 = _orientation(ax, ay, bx, by, px, py)
        d2 = _orientation(ax, ay, bx, by, qx, qy)
        d3 = _orientation(px, py, qx, qy, ax, ay)
        d4 = _orientation(px, py, qx, qy, bx, by)
        straddle = (d1 * d2 <= 0) & (d3 * d4 <= 0)
        # The orientation test alone accepts collinear segments that do not overlap: check the boxes too.
        boxes = (
            (np.maximum(px, qx) >= np.minimum(ax, bx))
            & (np.maximum(ax, bx) >= np.minimum(px, qx))
            & (np.maximum(py, qy) >= np.minimum(ay, by))
            & (np.maximum(ay, by) >= np.minimum(py, qy))
        )
        return straddle & boxes

    @staticmethod
    def crossing_fraction(px, py, qx, qy, ax, ay, bx, by) -> NDArray[np.float64]:
        """Where P→Q meets the line through A and B, as a fraction of P→Q (1 for parallel segments)."""
        rx, ry, sx, sy = qx - px, qy - py, bx - ax, by - ay
        denominator = rx * sy - ry * sx
        with np.errstate(divide="ignore", invalid="ignore"):
            t = ((ax - px) * sy - (ay - py) * sx) / denominator
        return np.where(denominator == 0, 1.0, np.clip(t, 0.0, 1.0))


def _orientation(ax, ay, bx, by, px, py):
    """Sign of the cross product (B − A) × (P − A): > 0 when P is left of A→B."""
    return (bx - ax) * (py - ay) - (by - ay) * (px - ax)
