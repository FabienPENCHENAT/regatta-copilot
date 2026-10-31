from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


class HeadingFan:
    """Candidate headings tried from every front point: every `step_deg` degrees, 0 included."""

    def __init__(self, step_deg: float = 5.0) -> None:
        if not 0 < step_deg <= 90:
            raise ValueError("heading step must be in (0, 90] degrees")
        self.headings_deg: NDArray[np.float64] = np.arange(0.0, 360.0, step_deg)
