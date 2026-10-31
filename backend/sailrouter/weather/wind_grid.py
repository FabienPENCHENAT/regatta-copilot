from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class WindGrid:
    """10 m wind on a regular lat/lon grid at one valid time.

    `lat_deg` and `lon_deg` are 1-D, strictly increasing and evenly spaced; `u_ms` / `v_ms` are indexed
    `[lat, lon]` (eastward / northward components, m/s).
    """

    valid_time: datetime
    lat_deg: NDArray[np.float64]
    lon_deg: NDArray[np.float64]
    u_ms: NDArray[np.float32]
    v_ms: NDArray[np.float32]

    def __post_init__(self) -> None:
        shape = (self.lat_deg.size, self.lon_deg.size)
        if self.u_ms.shape != shape or self.v_ms.shape != shape:
            raise ValueError(f"wind arrays {self.u_ms.shape}/{self.v_ms.shape} do not match grid {shape}")
