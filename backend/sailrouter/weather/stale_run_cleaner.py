from __future__ import annotations

import logging
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.run_download_lock import RunDownloadLock

CYCLE = timedelta(hours=6)
log = logging.getLogger(__name__)


class StaleRunCleaner:
    """Deletes the weather runs no longer needed (var/weather/ grew by ≈ 440 MB a day). For each model in use it
    keeps the run in use, `keep_previous` runs before it (a fallback if the newest proves damaged) and every
    newer run (one being downloaded); older run folders and their stale download locks go. A run another process
    is downloading is never touched."""

    def __init__(self, weather_dir: Path, keep_previous: int = 1) -> None:
        self._dir = weather_dir
        self._keep_previous = keep_previous
        self._locks = RunDownloadLock(weather_dir)

    def clean(self, in_use: list[ModelRun]) -> list[str]:
        removed = []
        for current in in_use:
            oldest_kept = current.cycle - CYCLE * self._keep_previous
            for path in sorted(self._dir.glob(f"{current.model}-*")):
                run = _run_of(path, current.model)
                if run is None or run.cycle >= oldest_kept or self._locks.held_by_other(run):
                    continue
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink(missing_ok=True)
                removed.append(path.name)
        if removed:
            log.info("removed %d old weather item(s): %s", len(removed), ", ".join(removed))
        return removed


def _run_of(path: Path, model: str) -> ModelRun | None:
    """The run a folder (`gefs-2026110100`) or a lock file (`gefs-2026110100.downloading`) belongs to."""
    stamp = path.name.split(".")[0].removeprefix(f"{model}-")
    try:
        return ModelRun(model, datetime.strptime(stamp, "%Y%m%d%H").replace(tzinfo=UTC))
    except ValueError:
        return None
