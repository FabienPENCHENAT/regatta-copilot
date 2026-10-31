from __future__ import annotations

from datetime import UTC, datetime, timedelta
from time import perf_counter
from typing import TextIO

from sailrouter.course.race_catalog import RaceCatalog
from sailrouter.service.ensemble_job_factory import build_ensemble_job
from sailrouter.service.project_paths import ProjectPaths


class EnsembleDownloadCommand:
    """`python -m sailrouter ensemble-download`: puts the latest complete GEFS run on disk for a race window,
    in the foreground, with progress (the web app then routes the 31 members without waiting)."""

    def __init__(self, paths: ProjectPaths, out: TextIO) -> None:
        self._paths = paths
        self._out = out

    def run(self, race_id: str, start: datetime | None, hours: float) -> int:
        race = RaceCatalog(self._paths.races_dir).load(race_id)
        start = start or max(race.start_time, datetime.now(UTC))
        end = start + timedelta(hours=hours)
        print(f"GEFS window {start:%Y-%m-%d %H:%M} → {end:%Y-%m-%d %H:%M} UTC", file=self._out)
        began = perf_counter()
        try:
            run = build_ensemble_job(self._paths).download(start, end, self._print_progress)
        except (ConnectionError, OSError) as error:
            print(f"\nError: {error}", file=self._out)
            return 1
        if run is None:
            print("No complete GEFS run found on NOMADS.", file=self._out)
            return 1
        print(f"\nGEFS run {run.key} ready in {perf_counter() - began:.0f} s", file=self._out)
        return 0

    def _print_progress(self, done: int, total: int) -> None:
        print(f"\rDownloading GEFS: {done}/{total} files", end="", file=self._out, flush=True)
