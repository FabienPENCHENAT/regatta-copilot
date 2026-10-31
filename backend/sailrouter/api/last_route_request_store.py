from __future__ import annotations

import json
import logging
import os
import threading
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from sailrouter.api.schemas import RouteRequest

log = logging.getLogger(__name__)


class LastRouteRequestStore:
    """The last route request received, in memory and on disk (`var/last_request.json`, survives a restart),
    with the time it was received: the background refresher computes it again when the weather changes."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._last: tuple[RouteRequest, datetime] | None = None

    def save(self, request: RouteRequest, received_at: datetime | None = None) -> None:
        received_at = received_at or datetime.now(UTC)
        with self._lock:
            self._last = (request, received_at)
            self._path.parent.mkdir(parents=True, exist_ok=True)
            entry = {"received_at": received_at.isoformat(), "request": request.model_dump()}
            temporary = self._path.with_suffix(".part")
            temporary.write_text(json.dumps(entry), encoding="utf-8")
            os.replace(temporary, self._path)

    def load(self) -> tuple[RouteRequest, datetime] | None:
        with self._lock:
            if self._last is None and self._path.is_file():
                self._last = self._read()
            return self._last

    def _read(self) -> tuple[RouteRequest, datetime] | None:
        try:
            entry = json.loads(self._path.read_text(encoding="utf-8"))
            return RouteRequest.model_validate(entry["request"]), datetime.fromisoformat(entry["received_at"])
        except (OSError, ValueError, KeyError, ValidationError) as error:
            log.warning("ignoring unreadable %s: %s", self._path, error)
            return None
