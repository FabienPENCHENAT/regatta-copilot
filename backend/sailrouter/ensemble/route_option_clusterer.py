from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


class RouteOptionClusterer:
    """Groups member routes into options from their pairwise distances (see `RouteDistanceMatrix`).

    1. Average-linkage agglomeration: the two closest groups merge while their mean distance is at most
       `threshold_nm`.
    2. Groups smaller than `min_members` (a lone member is noise, not a scenario) join their nearest group.
    3. While there are more than `max_options` groups, the smallest joins its nearest group.
    Deterministic: ties go to the lowest indices. Groups are returned largest first (ties: lowest member).
    """

    def __init__(self, threshold_nm: float = 70.0, min_members: int = 2, max_options: int = 4) -> None:
        self._threshold_nm = threshold_nm
        self._min_members = min_members
        self._max_options = max_options

    def cluster(self, distances_nm: NDArray) -> list[list[int]]:
        count = distances_nm.shape[0]
        if count == 0:
            return []
        groups = [[i] for i in range(count)]
        while len(groups) > 1:
            a, b, gap = self._closest_pair(groups, distances_nm)
            if gap > self._threshold_nm:
                break
            groups = self._merged(groups, a, b)
        groups = self._absorb(groups, distances_nm, lambda gs: len(min(gs, key=len)) < self._min_members)
        groups = self._absorb(groups, distances_nm, lambda gs: len(gs) > self._max_options)
        return sorted((sorted(g) for g in groups), key=lambda g: (-len(g), g[0]))

    def _absorb(self, groups: list[list[int]], distances_nm: NDArray, needed) -> list[list[int]]:
        """Merges the smallest group into its nearest one while `needed(groups)` holds."""
        while len(groups) > 1 and needed(groups):
            small = min(range(len(groups)), key=lambda k: (len(groups[k]), min(groups[k])))
            others = [k for k in range(len(groups)) if k != small]
            nearest = min(others, key=lambda k: (self._linkage(groups[small], groups[k], distances_nm), k))
            groups = self._merged(groups, small, nearest)
        return groups

    def _closest_pair(self, groups: list[list[int]], distances_nm: NDArray) -> tuple[int, int, float]:
        best = (0, 1, float("inf"))
        for a in range(len(groups)):
            for b in range(a + 1, len(groups)):
                gap = self._linkage(groups[a], groups[b], distances_nm)
                if gap < best[2]:
                    best = (a, b, gap)
        return best

    @staticmethod
    def _linkage(first: list[int], second: list[int], distances_nm: NDArray) -> float:
        return float(distances_nm[np.ix_(first, second)].mean())

    @staticmethod
    def _merged(groups: list[list[int]], a: int, b: int) -> list[list[int]]:
        merged = groups[a] + groups[b]
        return [g for k, g in enumerate(groups) if k not in (a, b)] + [merged]
