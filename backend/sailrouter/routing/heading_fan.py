from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


class HeadingFan:
    """Candidate headings tried from every front point: every `step_deg` degrees within `width_deg` centred on
    the bearing to the mark aimed at (110° each side by default, like routers made for the game). A width of
    360° tries the whole circle."""

    def __init__(self, step_deg: float = 1.0, width_deg: float = 220.0) -> None:
        if not 0 < step_deg <= 90:
            raise ValueError("heading step must be in (0, 90] degrees")
        if not 0 < width_deg <= 360:
            raise ValueError("fan width must be in (0, 360] degrees")
        if width_deg >= 360:
            self.offsets_deg: NDArray[np.float64] = np.arange(0.0, 360.0, step_deg)
        else:
            half = width_deg / 2
            self.offsets_deg = np.arange(-half, half + step_deg / 2, step_deg)

    def headings(self, bearing_deg: ArrayLike) -> NDArray[np.float64]:
        """Headings (degrees true) per point, shape (points, headings), around each point's bearing."""
        return np.mod(np.asarray(bearing_deg, float)[:, None] + self.offsets_deg[None, :], 360.0)
