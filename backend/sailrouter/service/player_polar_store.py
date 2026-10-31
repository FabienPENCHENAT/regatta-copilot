from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


class PlayerPolarStore:
    """The polars the player imported from the game, one per race and boat:
    `var/polars/<race>-<boat>.vr.json` (runtime data, git-ignored). The file's modification time is the import
    time."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def path(self, race_id: str, boat_id: str) -> Path:
        for value in (race_id, boat_id):
            if not SAFE_ID.match(value):
                raise ValueError(f"invalid id {value!r}")
        return self._directory / f"{race_id}-{boat_id}.vr.json"

    def has(self, race_id: str, boat_id: str) -> bool:
        return self.path(race_id, boat_id).is_file()

    def save(self, race_id: str, boat_id: str, polar: dict[str, Any]) -> Path:
        target = self.path(race_id, boat_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".part")
        temporary.write_text(json.dumps(polar, separators=(",", ":")), encoding="utf-8")
        os.replace(temporary, target)
        return target

    def delete(self, race_id: str, boat_id: str) -> bool:
        path = self.path(race_id, boat_id)
        existed = path.is_file()
        path.unlink(missing_ok=True)
        return existed

    def imported_at(self, race_id: str, boat_id: str) -> datetime | None:
        path = self.path(race_id, boat_id)
        return datetime.fromtimestamp(path.stat().st_mtime, UTC) if path.is_file() else None
