from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class ModelRun:
    """One forecast run of a model: `gfs` (deterministic) or `gefs` (ensemble), at a cycle time (00/06/12/18 UTC)."""

    model: str
    cycle: datetime

    def __post_init__(self) -> None:
        if self.cycle.tzinfo is None:
            raise ValueError("cycle must be timezone-aware (UTC)")
        if self.cycle.hour % 6 or self.cycle.minute or self.cycle.second:
            raise ValueError(f"not a model cycle: {self.cycle.isoformat()}")

    @property
    def key(self) -> str:
        """Stable identifier, e.g. `gfs-2026103106`, used for cache folders."""
        return f"{self.model}-{self.cycle.astimezone(UTC):%Y%m%d%H}"

    def hours_since_cycle(self, moment: datetime) -> float:
        return (moment - self.cycle).total_seconds() / 3600.0
