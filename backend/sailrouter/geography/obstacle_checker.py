from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from sailrouter.geography.land_mask import LandMask
from sailrouter.geography.zone_crossing_detector import ZoneCrossingDetector

SAMPLES_PER_CHUNK = 2_000_000  # bounds memory: a few arrays of this many samples at a time


class ObstacleChecker:
    """Whether segments (straight in lat/lon) cross land, leave the raster area or enter an exclusion zone.

    Land is checked by sampling each segment: first every half coarse cell against the dilated coarse mask
    (cheap, conservative), then every half fine cell, only for the segments that may be near land.
    """

    def __init__(self, land: LandMask, zones: ZoneCrossingDetector) -> None:
        self._land = land
        self._zones = zones

    def blocked(self, lat0: ArrayLike, lon0: ArrayLike, lat1: ArrayLike, lon1: ArrayLike) -> NDArray[np.bool_]:
        lat0, lon0, lat1, lon1 = (np.asarray(a, float).ravel() for a in (lat0, lon0, lat1, lon1))
        blocked = self._zones.blocked(lat0, lon0, lat1, lon1)
        coarse_step = self._land.coarse_grid.resolution_deg / 2
        maybe = ~blocked & self._any_sample(self._land.may_be_near_land, lat0, lon0, lat1, lon1, coarse_step)
        if maybe.any():
            idx = np.nonzero(maybe)[0]
            fine_step = self._land.grid.resolution_deg / 2
            blocked[idx] = self._any_sample(self._land.is_land, lat0[idx], lon0[idx], lat1[idx], lon1[idx], fine_step)
        return blocked

    @staticmethod
    def _any_sample(test, lat0, lon0, lat1, lon1, step_deg: float) -> NDArray[np.bool_]:
        """True where `test` is true at any of the evenly spaced samples (ends included) of a segment."""
        result = np.zeros(lat0.size, dtype=bool)
        if lat0.size == 0:
            return result
        span = np.maximum(np.abs(lat1 - lat0), np.abs(lon1 - lon0))
        n_samples = max(int(np.ceil(span.max() / step_deg)) + 1, 2)
        t = np.linspace(0.0, 1.0, n_samples)[None, :]
        chunk = max(1, SAMPLES_PER_CHUNK // n_samples)
        for start in range(0, lat0.size, chunk):
            part = slice(start, start + chunk)
            lat = lat0[part, None] + (lat1 - lat0)[part, None] * t
            lon = lon0[part, None] + (lon1 - lon0)[part, None] * t
            result[part] = test(lat, lon).any(axis=1)
        return result
