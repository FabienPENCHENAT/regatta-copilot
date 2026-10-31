from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

from sailrouter.weather.model_run import ModelRun


class ForecastStore:
    """On-disk cache of downloaded GRIB files: `<root>/<run key>/f<lead>.grib2`.

    A lead time is downloaded once per run; later calls read the file. Files are written atomically
    (temporary file + rename) so an interrupted download never leaves a truncated GRIB behind.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    def path(self, run: ModelRun, lead_h: int, member: str = "") -> Path:
        suffix = f"-{member}" if member else ""
        return self._root / run.key / f"f{lead_h:03d}{suffix}.grib2"

    def has(self, run: ModelRun, lead_h: int, member: str = "") -> bool:
        return self.path(run, lead_h, member).is_file()

    def missing(self, run: ModelRun, lead_hours: Sequence[int], members: Sequence[str]) -> list[tuple[int, str]]:
        """(lead, member) pairs not on disk yet, lead by lead."""
        return [(lead, member) for lead in lead_hours for member in members if not self.has(run, lead, member)]

    def write(self, run: ModelRun, lead_h: int, content: bytes, member: str = "") -> Path:
        target = self.path(run, lead_h, member)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".part")
        temporary.write_bytes(content)
        os.replace(temporary, target)
        return target

    def cached_runs(self) -> list[str]:
        """Run keys present on disk, newest first."""
        if not self._root.is_dir():
            return []
        return sorted((p.name for p in self._root.iterdir() if p.is_dir()), reverse=True)
