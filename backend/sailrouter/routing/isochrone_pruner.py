from __future__ import annotations

from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray

from sailrouter.domain.great_circle import GreatCircle
from sailrouter.routing.isochrone import Isochrone
from sailrouter.routing.mark_progress import MarkProgress


class IsochronePruner:
    """Thins a front of candidates to its outer envelope.

    1. Only the points on the most advanced leg are kept: once a point has passed a mark, the points that
       have not are dropped (V1 simplification, costs at most one step at a mark).
    2. Sectors of `sector_deg` are taken by bearing from the leg ANCHOR (start or last mark passed); in each
       sector the point farthest from the anchor is kept. Using the anchor rather than the next mark keeps
       the true time envelope, so dead ends (bays such as Saint-Brieuc) cannot trap the front.
3. Points whose segment is blocked (land, forbidden zone) are dropped first; see `prune`.
    """

    def __init__(self, sector_deg: float = 0.5) -> None:
        if sector_deg <= 0:
            raise ValueError("sector width must be positive")
        self._sector_deg = sector_deg

    def prune(self, candidates: Isochrone, progress: MarkProgress,
              blocked: Callable[[NDArray[np.intp]], NDArray[np.bool_]] | None = None) -> Isochrone:
        """The envelope of the candidates whose segment is not `blocked`. `blocked(indices)` is only asked about
        candidates that can still win their sector, farthest first: checking every segment against land is the
        costliest part of a step, and most candidates lose to a farther one anyway."""
        blocked = blocked or (lambda indices: np.zeros(indices.size, dtype=bool))
        for leg in np.unique(candidates.leg)[::-1]:  # the most advanced leg that keeps at least one point
            on_leg = np.nonzero(candidates.leg == leg)[0]
            if leg >= progress.finished_leg:
                kept = on_leg[~blocked(on_leg)]
            else:
                kept = self._farthest_free_by_sector(candidates, on_leg, progress.legs[int(leg)].anchor, blocked)
            if kept.size:
                return candidates.subset(kept)
        return candidates.subset(np.zeros(0, dtype=np.intp))

    def _farthest_free_by_sector(self, candidates: Isochrone, on_leg: NDArray[np.intp], anchor,
                                 blocked: Callable[[NDArray[np.intp]], NDArray[np.bool_]]) -> NDArray[np.intp]:
        """Per sector (ascending), the farthest candidate from the anchor that is not blocked. Candidates are
        checked by rounds of growing depth (1, 4, 16... per sector) until every sector has its winner."""
        lat, lon = candidates.lat_deg[on_leg], candidates.lon_deg[on_leg]
        bearing = GreatCircle.bearing_deg(anchor.lat_deg, anchor.lon_deg, lat, lon)
        distance = GreatCircle.distance_nm(anchor.lat_deg, anchor.lon_deg, lat, lon)
        sector = np.floor(bearing / self._sector_deg).astype(np.int64)
        order = np.lexsort((-distance, sector))
        ordered, sector = on_leg[order], sector[order]
        new_sector = np.ones(order.size, dtype=bool)
        new_sector[1:] = sector[1:] != sector[:-1]
        group = np.cumsum(new_sector) - 1
        rank = np.arange(order.size) - np.nonzero(new_sector)[0][group]
        winner = np.full(int(group[-1]) + 1, -1, dtype=np.intp)
        low, depth = 0, 1
        while True:
            asked = np.nonzero((winner[group] < 0) & (rank >= low) & (rank < low + depth))[0]
            if asked.size == 0:
                return winner[winner >= 0]
            free = asked[~blocked(ordered[asked])]
            groups, first = np.unique(group[free], return_index=True)  # free is in (sector, rank) order
            winner[groups] = ordered[free[first]]
            low, depth = low + depth, depth * 4
