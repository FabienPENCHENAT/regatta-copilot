from __future__ import annotations

import numpy as np

from sailrouter.domain.geo_point import GeoPoint
from sailrouter.ensemble.advice_writer import AdviceWriter
from sailrouter.ensemble.confidence_grader import ConfidenceGrader
from sailrouter.ensemble.eta_gap_estimator import EtaGapEstimator
from sailrouter.ensemble.medoid_picker import MedoidPicker
from sailrouter.ensemble.option_labeler import OptionLabeler
from sailrouter.ensemble.route_distance_matrix import RouteDistanceMatrix
from sailrouter.ensemble.route_option import EnsembleSynthesis, RouteOption
from sailrouter.ensemble.route_option_clusterer import RouteOptionClusterer
from sailrouter.routing.mark_progress import MarkProgress
from sailrouter.routing.route import Route

PLAN_HOURS = (4, 8, 12, 16, 24, 48)


class EnsembleSynthesizer:
    """Turns the member routes (one per GEFS member) into route options: groups → representative route →
    name and kind → probability, confidence, arrival gap; flags the option the game's route (GFS) falls in."""

    def __init__(
        self, distances: RouteDistanceMatrix | None = None, clusterer: RouteOptionClusterer | None = None,
        labeler: OptionLabeler | None = None,
    ) -> None:
        self._distances = distances or RouteDistanceMatrix()
        self._clusterer = clusterer or RouteOptionClusterer()
        self._labeler = labeler or OptionLabeler()
        self._medoids = MedoidPicker()
        self._confidence = ConfidenceGrader()
        self._eta = EtaGapEstimator()

    def synthesize(self, member_routes: dict[str, Route], game_route: Route, progress: MarkProgress) -> EnsembleSynthesis:
        if not member_routes:
            raise ValueError("no member route to synthesize")
        names, routes = list(member_routes), list(member_routes.values())
        all_distances = self._distances.distances_nm([*routes, game_route])
        distances, game_row = all_distances[:-1, :-1], all_distances[-1, :-1]
        groups = self._clusterer.cluster(distances)
        representatives = [self._medoids.pick(group, distances) for group in groups]
        late = self._distances.positions(routes, self._distances.late_h)
        consensus = (float(np.median(late[:, 0])), float(np.median(late[:, 1])))
        labels = self._labeler.label([tuple(late[r]) for r in representatives], consensus, self._course(routes, progress))
        game_member = int(np.argmin(game_row))
        gaps = self._eta.gaps_h([routes[r] for r in representatives])
        options = tuple(
            RouteOption(
                id=name, kind=kind, members=tuple(names[i] for i in group), representative=names[rep],
                route=routes[rep], probability=len(group) / len(routes), game_route=game_member in group,
                eta_delta_h=gap, confidence_by_hour=self._confidences(routes[rep], [routes[i] for i in group]),
            )
            for group, rep, (name, kind), gap in zip(groups, representatives, labels, gaps)
        )
        member_options = {member: option.id for option in options for member in option.members}
        return EnsembleSynthesis(options, member_options, len(routes), AdviceWriter().advice(list(options), len(routes)))

    def _confidences(self, representative: Route, members: list[Route]) -> dict[int, float]:
        return {hour: self._confidence.confidence(representative, members, hour)
                for hour in PLAN_HOURS if representative.covers(hour)}

    def _course(self, routes: list[Route], progress: MarkProgress) -> tuple[GeoPoint, GeoPoint]:
        """Anchor and target of the leg most members are on at +48 h (the next mark that matters)."""
        passed = [route.point_at(self._distances.late_h).marks_passed for route in routes]
        leg = progress.legs[min(int(np.median(passed)), len(progress.legs) - 1)]
        return leg.anchor, leg.target
