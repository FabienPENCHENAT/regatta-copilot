from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RoutePoint:
    """A position of the route at `time`, and what to set from there until the next point.

    `heading_deg`, `twa_deg` (signed, positive = wind on starboard), `tws_kn`, `sail` and `speed_kn` describe
    the leg that starts here; they are None on the last point. `marks_passed` counts the course legs done.
    """

    time: datetime
    lat_deg: float
    lon_deg: float
    marks_passed: int
    heading_deg: float | None = None
    twa_deg: float | None = None
    tws_kn: float | None = None
    sail: str | None = None
    speed_kn: float | None = None
