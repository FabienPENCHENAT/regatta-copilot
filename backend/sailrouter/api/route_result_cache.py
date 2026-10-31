from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

KEEP_FOR = timedelta(days=2)  # older files are deleted when a new result is stored


class RouteResultCache:
    """Computed route results kept on disk (var/results/), so reopening the site with the same inputs and the
    same weather runs is instant. The key holds everything a route depends on, including the weather run ids:
    a new forecast run gives a new key, hence one fresh computation, then instant answers until the next run."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    @staticmethod
    def key(inputs: dict) -> str:
        canonical = json.dumps(inputs, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:32]

    def get(self, key: str, now: datetime | None = None) -> dict | None:
        path = self._directory / f"{key}.json"
        if not path.is_file():
            return None
        entry = json.loads(path.read_text(encoding="utf-8"))
        expires = entry.get("expires_at")
        if expires and datetime.fromisoformat(expires) <= (now or datetime.now(UTC)):
            return None
        return entry["result"]

    def put(self, key: str, result: dict, expires_at: datetime | None = None) -> None:
        self._directory.mkdir(parents=True, exist_ok=True)
        entry = {"stored_at": datetime.now(UTC).isoformat(), "expires_at": expires_at.isoformat() if expires_at else None,
                 "result": result}
        (self._directory / f"{key}.json").write_text(json.dumps(entry, separators=(",", ":")), encoding="utf-8")
        self._forget_old()

    def _forget_old(self) -> None:
        limit = datetime.now(UTC).timestamp() - KEEP_FOR.total_seconds()
        for path in self._directory.glob("*.json"):
            if path.stat().st_mtime < limit:
                path.unlink(missing_ok=True)
