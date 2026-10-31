from __future__ import annotations

from dataclasses import dataclass, field

from sailrouter.routing.route import Route


@dataclass(frozen=True)
class RouteOption:
    """One route option: the GEFS members whose routes go the same way, and the member route shown for it.

    `probability` = members of the option / members routed. `confidence_by_hour` holds the route-plan
    confidence at each plan hour (see `ConfidenceGrader`).
    """

    id: str
    kind: str
    members: tuple[str, ...]
    representative: str
    route: Route
    probability: float
    game_route: bool
    eta_delta_h: float
    confidence_by_hour: dict[int, float] = field(default_factory=dict)


@dataclass(frozen=True)
class EnsembleSynthesis:
    """The options found (most probable first), which option each member belongs to, and the advice."""

    options: tuple[RouteOption, ...]
    member_options: dict[str, str]
    member_total: int
    advice: dict

    @property
    def recommended(self) -> RouteOption:
        return self.options[0]
