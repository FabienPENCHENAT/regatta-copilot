from __future__ import annotations

import numpy as np

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
    """

    def __init__(self, sector_deg: float = 0.5) -> None:
        if sector_deg <= 0:
            raise ValueError("sector width must be positive")
        self._sector_deg = sector_deg

    def prune(self, candidates: Isochrone, progress: MarkProgress) -> Isochrone:
        if len(candidates) == 0:
            return candidates
        top_leg = int(candidates.leg.max())
        on_top = np.nonzero(candidates.leg == top_leg)[0]
        if top_leg >= progress.finished_leg:
            return candidates.subset(on_top)
        anchor = progress.legs[top_leg].anchor
        lat, lon = candidates.lat_deg[on_top], candidates.lon_deg[on_top]
        bearing = GreatCircle.bearing_deg(anchor.lat_deg, anchor.lon_deg, lat, lon)
        distance = GreatCircle.distance_nm(anchor.lat_deg, anchor.lon_deg, lat, lon)
        sector = np.floor(bearing / self._sector_deg).astype(np.int64)
        order = np.lexsort((-distance, sector))
        first_of_sector = np.ones(order.size, dtype=bool)
        first_of_sector[1:] = sector[order][1:] != sector[order][:-1]
        return candidates.subset(on_top[order[first_of_sector]])
