from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Isochrone:
    """One front of reachable positions at `time`.

    Per point: position, index of its `parent` in the previous isochrone (−1 for the start), and the
    segment that led to it — heading, signed TWA (positive = wind on starboard), TWS, sail index and boat
    speed, all taken at the parent — plus `leg`, the index of the next mark to pass.
    """

    time: datetime
    lat_deg: NDArray[np.float64]
    lon_deg: NDArray[np.float64]
    parent: NDArray[np.intp]
    heading_deg: NDArray[np.float64]
    twa_deg: NDArray[np.float64]
    tws_kn: NDArray[np.float64]
    sail: NDArray[np.int8]
    speed_kn: NDArray[np.float64]
    leg: NDArray[np.int16]

    @classmethod
    def origin(cls, time: datetime, lat_deg: float, lon_deg: float) -> Isochrone:
        nan = np.array([np.nan])
        return cls(
            time=time,
            lat_deg=np.array([lat_deg]),
            lon_deg=np.array([lon_deg]),
            parent=np.array([-1], dtype=np.intp),
            heading_deg=nan,
            twa_deg=nan.copy(),
            tws_kn=nan.copy(),
            sail=np.array([-1], dtype=np.int8),
            speed_kn=nan.copy(),
            leg=np.array([0], dtype=np.int16),
        )

    def __len__(self) -> int:
        return int(self.lat_deg.size)

    def subset(self, indices: NDArray[np.intp]) -> Isochrone:
        return Isochrone(
            time=self.time,
            lat_deg=self.lat_deg[indices],
            lon_deg=self.lon_deg[indices],
            parent=self.parent[indices],
            heading_deg=self.heading_deg[indices],
            twa_deg=self.twa_deg[indices],
            tws_kn=self.tws_kn[indices],
            sail=self.sail[indices],
            speed_kn=self.speed_kn[indices],
            leg=self.leg[indices],
        )
