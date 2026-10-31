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
    """

    def __init__(self, land: LandMask, zones: ZoneCrossingDetector) -> None:
        self._land = land
        self._zones = zones

    def blocked(self, lat0: ArrayLike, lon0: ArrayLike, lat1: ArrayLike, lon1: ArrayLike) -> NDArray[np.bool_]:
        lat0, lon0, lat1, lon1 = (np.asarray(a, float).ravel() for a in (lat0, lon0, lat1, lon1))
        blocked = self._zones.blocked(lat0, lon0, lat1, lon1)
        span = np.maximum(np.abs(lat1 - lat0), np.abs(lon1 - lon0))
        clear = np.maximum(self._land.clearance_deg(lat0, lon0), self._land.clearance_deg(lat1, lon1)) > span
        idx = np.nonzero(~blocked & ~clear)[0]
        coarse_step = self._land.coarse_grid.resolution_deg / 2
        maybe = self._any_sample(self._land.may_be_near_land, lat0[idx], lon0[idx], lat1[idx], lon1[idx], coarse_step)
        idx = idx[maybe]
        fine_step = self._land.grid.resolution_deg / 2
        blocked[idx] = self._any_sample(self._land.is_land, lat0[idx], lon0[idx], lat1[idx], lon1[idx], fine_step)
        return blocked

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
