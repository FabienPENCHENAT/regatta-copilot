from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from sailrouter.geography.land_mask import LandMask
from sailrouter.geography.zone_crossing_detector import ZoneCrossingDetector

SAMPLES_PER_CHUNK = 2_000_000  # bounds memory: a few arrays of this many samples at a time


class ObstacleChecker:
    """Whether segments (straight in lat/lon) cross land, leave the raster area or enter an exclusion zone.

    Land: a segment shorter than the clearance around one of its ends cannot touch land and is skipped (most
    open-ocean segments). The others are sampled, first every half coarse cell against the dilated coarse mask
    (cheap, conservative), then every half fine cell, only for the segments that may be near land. Segments are
    sampled in groups of similar length, so a few long ones do not make every segment expensive.

    With a `margin` mask (land widened by `CoastMargin`), segments may not enter the margin either, except those
    starting inside it, which are only checked against real land so the boat can get out.
    """

    def __init__(self, land: LandMask, zones: ZoneCrossingDetector, margin: LandMask | None = None) -> None:
        self._land = land
        self._zones = zones
        self._margin = margin

    def blocked(self, lat0: ArrayLike, lon0: ArrayLike, lat1: ArrayLike, lon1: ArrayLike) -> NDArray[np.bool_]:
        lat0, lon0, lat1, lon1 = (np.asarray(a, float).ravel() for a in (lat0, lon0, lat1, lon1))
        blocked = self._zones.blocked(lat0, lon0, lat1, lon1)
        todo = np.nonzero(~blocked)[0]
        if self._margin is None:
            blocked[todo] = self._crosses(self._land, lat0[todo], lon0[todo], lat1[todo], lon1[todo])
            return blocked
        # The coast margin may not be entered; a boat already inside it (start, anchorage) only avoids real land.
        inside = self._margin.is_land(lat0[todo], lon0[todo])
        for land, part in ((self._margin, todo[~inside]), (self._land, todo[inside])):
            blocked[part] = self._crosses(land, lat0[part], lon0[part], lat1[part], lon1[part])
        return blocked

    def _crosses(self, land: LandMask, lat0, lon0, lat1, lon1) -> NDArray[np.bool_]:
        span = np.maximum(np.abs(lat1 - lat0), np.abs(lon1 - lon0))
        clear = np.maximum(land.clearance_deg(lat0, lon0), land.clearance_deg(lat1, lon1)) > span
        crosses = np.zeros(lat0.size, dtype=bool)
        idx = np.nonzero(~clear)[0]
        coarse_step = land.coarse_grid.resolution_deg / 2
        maybe = self._any_sample(land.may_be_near_land, lat0[idx], lon0[idx], lat1[idx], lon1[idx], coarse_step)
        idx = idx[maybe]
        fine_step = land.grid.resolution_deg / 2
        crosses[idx] = self._any_sample(land.is_land, lat0[idx], lon0[idx], lat1[idx], lon1[idx], fine_step)
        return crosses

    @staticmethod
    def _any_sample(test, lat0, lon0, lat1, lon1, step_deg: float) -> NDArray[np.bool_]:
        """True where `test` is true at any of the evenly spaced samples (ends included) of a segment.
        Segments are grouped by sample count rounded up to a power of two."""
        result = np.zeros(lat0.size, dtype=bool)
        if lat0.size == 0:
            return result
        span = np.maximum(np.abs(lat1 - lat0), np.abs(lon1 - lon0))
        needed = np.maximum(np.ceil(span / step_deg).astype(int) + 1, 2)
        bucket = 2 ** np.ceil(np.log2(needed)).astype(int)
        for n_samples in np.unique(bucket):
            members = np.nonzero(bucket == n_samples)[0]
            t = np.linspace(0.0, 1.0, int(n_samples))[None, :]
            chunk = max(1, SAMPLES_PER_CHUNK // int(n_samples))
            for start in range(0, members.size, chunk):
                part = members[start : start + chunk]
                lat = lat0[part, None] + (lat1 - lat0)[part, None] * t
                lon = lon0[part, None] + (lon1 - lon0)[part, None] * t
                result[part] = test(lat, lon).any(axis=1)
        return result
