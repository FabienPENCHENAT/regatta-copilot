from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

EARTH_RADIUS_NM = 3440.065


class GreatCircle:
    """Distance, initial bearing and destination point on a spherical Earth.

    Every method accepts scalars or numpy arrays (broadcast together). Degrees in, degrees out; distances in
    nautical miles.
    """

    @staticmethod
    def distance_nm(lat1: ArrayLike, lon1: ArrayLike, lat2: ArrayLike, lon2: ArrayLike) -> NDArray:
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = phi2 - phi1
        dlmb = np.radians(np.asarray(lon2) - np.asarray(lon1))
        a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlmb / 2) ** 2
        return 2 * EARTH_RADIUS_NM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))

    @staticmethod
    def bearing_deg(lat1: ArrayLike, lon1: ArrayLike, lat2: ArrayLike, lon2: ArrayLike) -> NDArray:
        """Initial true bearing from point 1 to point 2, in [0, 360)."""
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dlmb = np.radians(np.asarray(lon2) - np.asarray(lon1))
        y = np.sin(dlmb) * np.cos(phi2)
        x = np.cos(phi1) * np.sin(phi2) - np.sin(phi1) * np.cos(phi2) * np.cos(dlmb)
        return np.degrees(np.arctan2(y, x)) % 360.0

    @staticmethod
    def destination(
        lat: ArrayLike, lon: ArrayLike, bearing_deg: ArrayLike, distance_nm: ArrayLike
    ) -> tuple[NDArray, NDArray]:
        """Point reached after `distance_nm` on the initial `bearing_deg`. Longitude in [-180, 180)."""
        phi1, lmb1 = np.radians(lat), np.radians(lon)
        theta = np.radians(bearing_deg)
        delta = np.asarray(distance_nm) / EARTH_RADIUS_NM
        sin_phi2 = np.sin(phi1) * np.cos(delta) + np.cos(phi1) * np.sin(delta) * np.cos(theta)
        phi2 = np.arcsin(np.clip(sin_phi2, -1.0, 1.0))
        lmb2 = lmb1 + np.arctan2(
            np.sin(theta) * np.sin(delta) * np.cos(phi1), np.cos(delta) - np.sin(phi1) * sin_phi2
        )
        lon2 = (np.degrees(lmb2) + 180.0) % 360.0 - 180.0
        return np.degrees(phi2), lon2
