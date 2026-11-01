from __future__ import annotations

from dataclasses import dataclass, field

from sailrouter.ensemble.route_option import EnsembleSynthesis
from sailrouter.routing.route import Route
from sailrouter.service.route_report import RouteReport
from sailrouter.weather.model_run import ModelRun


@dataclass(frozen=True)
class EnsembleReport:
    """Result of one ensemble run: the game's route (deterministic GFS), every GEFS member route, the options,
    and how each option's track fares in every member's weather."""

    game: RouteReport
    gefs_run: ModelRun
    member_routes: dict[str, Route]
    synthesis: EnsembleSynthesis
    timings_s: dict[str, float] = field(default_factory=dict)
    # Cross-evaluation: outlook[option index][member] = {hour: distance to go (nm)} when the option's track is
    # sailed in that member's wind (see TrackFollower).
    outlook: list[dict[str, dict[float, float]]] = field(default_factory=list)
