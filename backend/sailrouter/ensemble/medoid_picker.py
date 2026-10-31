from __future__ import annotations

from collections.abc import Sequence

from numpy.typing import NDArray


class MedoidPicker:
    """Picks the member that best represents a group: the one with the smallest total distance to the others
    (ties: lowest index). Its route is a real route, unlike an average of positions."""

    def pick(self, group: Sequence[int], distances_nm: NDArray) -> int:
        return min(group, key=lambda i: (float(distances_nm[i, list(group)].sum()), i))
