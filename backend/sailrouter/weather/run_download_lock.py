from __future__ import annotations

import os
import time
from pathlib import Path

from sailrouter.weather.model_run import ModelRun


class RunDownloadLock:
    """Marks a run as "being downloaded" on disk so that two processes (the web server and the command line)
    never download the same run at once, which NOMADS would treat as abuse.

    The lock is a file next to the run folder holding the owner's process id, touched on every downloaded
    file; it counts as held while it was touched less than `stale_after_s` ago (a crashed download frees it).
    """

    def __init__(self, root: Path, stale_after_s: float = 120.0) -> None:
        self._root = root
        self._stale_after_s = stale_after_s

    def path(self, run: ModelRun) -> Path:
        return self._root / f"{run.key}.downloading"

    def held_by_other(self, run: ModelRun) -> bool:
        path = self.path(run)
        try:
            fresh = time.time() - path.stat().st_mtime < self._stale_after_s
            return fresh and path.read_text().strip() != str(os.getpid())
        except FileNotFoundError:
            return False

    def touch(self, run: ModelRun) -> None:
        path = self.path(run)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(os.getpid()))

    def release(self, run: ModelRun) -> None:
        self.path(run).unlink(missing_ok=True)
