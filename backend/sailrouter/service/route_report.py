from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sailrouter.domain.geo_point import GeoPoint
from sailrouter.routing.mark_progress import MarkProgress
from sailrouter.routing.route import Route
from sailrouter.weather.model_run import ModelRun


@dataclass(frozen=True)
class RouteReport:
    """Everything the CLI prints and writes about one routing run."""

    race_id: str
    race_name: str
    boat_id: str
    position: GeoPoint
    computed_at: datetime
    weather_run: ModelRun
    next_run_expected: datetime
    progress: MarkProgress
    route: Route
    step_count: int
    timings_s: dict[str, float] = field(default_factory=dict)
