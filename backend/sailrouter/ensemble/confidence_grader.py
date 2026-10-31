from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from sailrouter.domain.great_circle import GreatCircle
from sailrouter.routing.route import Route


class ConfidenceGrader:
    """Confidence of a route-plan step: the share of the option's members that are within the step's zone
    radius of the representative position at that hour. The zone grows with time (3 nm + 0.9 nm per hour:
    14 nm at +12 h, 46 nm at +48 h), as forecasts and boats drift apart."""

    @staticmethod
    def zone_radius_nm(hour: float) -> int:
        return round(3 + hour * 0.9)

    def confidence(self, representative: Route, members: Sequence[Route], hour: float) -> float:
        if not members:
            return 0.0
        lat0, lon0 = representative.position_at(hour)
        points = np.array([route.position_at(hour) for route in members])
        gaps = GreatCircle.distance_nm(lat0, lon0, points[:, 0], points[:, 1])
        return float(np.mean(gaps <= self.zone_radius_nm(hour)))
