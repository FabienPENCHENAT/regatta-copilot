from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from sailrouter.domain.great_circle import GreatCircle
from sailrouter.routing.route import Route


class RouteDistanceMatrix:
    """How far apart routes are, pairwise: the larger of their gap at +48 h and twice their gap at +24 h (nm).

    Doubling the 24 h gap puts both horizons on the same scale (routes diverge roughly linearly), so two
    routes that split early and meet again at 48 h still count as different.
    """

    def __init__(self, early_h: float = 24.0, late_h: float = 48.0) -> None:
        self.early_h = early_h
        self.late_h = late_h

    def positions(self, routes: Sequence[Route], hours: float) -> NDArray:
        """(N, 2) array of (lat, lon) at `hours` after the start."""
        return np.array([route.position_at(hours) for route in routes], dtype=float).reshape(-1, 2)

    def distances_nm(self, routes: Sequence[Route]) -> NDArray:
        early = self._pairwise(self.positions(routes, self.early_h))
        late = self._pairwise(self.positions(routes, self.late_h))
        return np.maximum(late, early * (self.late_h / self.early_h))

    @staticmethod
    def _pairwise(points: NDArray) -> NDArray:
        lat, lon = points[:, 0], points[:, 1]
        return GreatCircle.distance_nm(lat[:, None], lon[:, None], lat[None, :], lon[None, :])
