from __future__ import annotations

from collections.abc import Sequence

from sailrouter.domain.great_circle import GreatCircle
from sailrouter.routing.route import Route


class EtaGapEstimator:
    """Approximate arrival gap of each route against the best one, in hours.

    The routes stop at the horizon (120 h), far from the finish, so the arrival is extrapolated: time sailed
    + distance still to go ÷ the route's own mean speed. The gap mostly reflects the distance to go at the
    horizon; it ignores the weather after the horizon.
    """

    def gaps_h(self, routes: Sequence[Route]) -> list[float]:
        etas = [self.eta_h(route) for route in routes]
        best = min(etas)
        return [eta - best for eta in etas]

    @staticmethod
    def eta_h(route: Route) -> float:
        lat = [p.lat_deg for p in route.points]
        lon = [p.lon_deg for p in route.points]
        sailed_nm = float(GreatCircle.distance_nm(lat[:-1], lon[:-1], lat[1:], lon[1:]).sum()) if len(lat) > 1 else 0.0
        hours = route.duration_h
        if route.finished or route.distance_to_go_nm <= 0:
            return hours
        mean_speed_kn = sailed_nm / hours if hours > 0 and sailed_nm > 0 else 1.0
        return hours + route.distance_to_go_nm / mean_speed_kn
