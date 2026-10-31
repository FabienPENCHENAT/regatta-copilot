from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from sailrouter.routing.isochrone import Isochrone
from sailrouter.routing.mark_progress import MarkProgress
from sailrouter.routing.route import Route
from sailrouter.routing.route_point import RoutePoint


class RouteTracer:
    """Picks the best point of the last isochrone (most marks passed, then least distance to go) and walks
    the parents back to the start to build the `Route`."""

    def __init__(self, sail_names: Sequence[str]) -> None:
        self._sail_names = tuple(sail_names)

    def trace(self, fronts: Sequence[Isochrone], progress: MarkProgress) -> Route:
        last = fronts[-1]
        to_go = progress.distance_to_go_nm(last.leg, last.lat_deg, last.lon_deg)
        best = int(np.lexsort((to_go, -last.leg.astype(np.int64)))[0])
        chain = self._chain(fronts, best)
        points = []
        for k, (front, index) in enumerate(chain):
            leaving = chain[k + 1] if k + 1 < len(chain) else None
            points.append(self._point(front, index, leaving))
        return Route(tuple(points), float(to_go[best]), bool(last.leg[best] >= progress.finished_leg))

    @staticmethod
    def _chain(fronts: Sequence[Isochrone], best: int) -> list[tuple[Isochrone, int]]:
        chain = [(fronts[-1], best)]
        for front in reversed(fronts[:-1]):
            child, child_index = chain[-1]
            chain.append((front, int(child.parent[child_index])))
        return chain[::-1]

    def _point(self, front: Isochrone, index: int, leaving: tuple[Isochrone, int] | None) -> RoutePoint:
        base = dict(
            time=front.time,
            lat_deg=float(front.lat_deg[index]),
            lon_deg=float(front.lon_deg[index]),
            marks_passed=int(front.leg[index]),
        )
        if leaving is None:
            return RoutePoint(**base)
        next_front, next_index = leaving
        return RoutePoint(
            **base,
            heading_deg=float(next_front.heading_deg[next_index]),
            twa_deg=float(next_front.twa_deg[next_index]),
            tws_kn=float(next_front.tws_kn[next_index]),
            sail=self._sail_names[int(next_front.sail[next_index])],
            speed_kn=float(next_front.speed_kn[next_index]),
        )
