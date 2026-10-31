from __future__ import annotations

from dataclasses import dataclass

from sailrouter.weather.model_run import ModelRun

READY, DOWNLOADING, UNAVAILABLE = "ready", "downloading", "unavailable"


@dataclass(frozen=True)
class EnsembleStatus:
    """Where the GEFS ensemble stands: `ready` (a run is on disk for the window), `downloading` (`done` of
    `total` files) or `unavailable` (nothing usable yet, or NOMADS failed: see `error`)."""

    state: str
    run: ModelRun | None
    done: int
    total: int
    member_count: int
    error: str | None = None
