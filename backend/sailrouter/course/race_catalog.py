from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sailrouter.domain.exclusion_zone import ExclusionZone
from sailrouter.domain.geo_point import GeoPoint
from sailrouter.domain.mark import Mark
from sailrouter.domain.race import Race
from sailrouter.domain.race_boat import RaceBoat


class RaceFileError(ValueError):
    """A race file is missing, unreadable or does not follow the format of docs/ai/api-contract.md."""


class RaceCatalog:
    """Lists and loads the race files of a directory (`races/<id>.json`, coordinates as `[lat, lon]`)."""

    def __init__(self, races_dir: Path) -> None:
        self._races_dir = races_dir

    def race_ids(self) -> list[str]:
        return sorted(path.stem for path in self._races_dir.glob("*.json"))

    def load(self, race_id: str) -> Race:
        path = self._races_dir / f"{race_id}.json"
        if not path.is_file():
            raise RaceFileError(f"unknown race {race_id!r} (known: {', '.join(self.race_ids())})")
        try:
            return self._build_race(json.loads(path.read_text(encoding="utf-8")))
        except (KeyError, TypeError, ValueError) as error:
            raise RaceFileError(f"{path.name}: {error}") from error

    def _build_race(self, data: dict[str, Any]) -> Race:
        return Race(
            id=data["id"],
            name=data["name"],
            start_time=_parse_time(data["start_time_utc"]),
            close_time=_parse_time(data["close_time_utc"]),
            default_boat=data["default_boat"],
            boats=tuple(self._build_boat(boat) for boat in data["boats"]),
            marks=tuple(self._build_mark(mark) for mark in data["marks"]),
            finish=self._build_finish(data["finish"]),
            exclusion_zones=tuple(self._build_zone(zone) for zone in data.get("exclusion_zones", [])),
        )

    @staticmethod
    def _build_boat(data: dict[str, Any]) -> RaceBoat:
        a, b = (GeoPoint.from_lat_lon(point) for point in data["start_line"])
        return RaceBoat(id=data["id"], polar_path=data.get("polar"), start_line=(a, b))

    @staticmethod
    def _build_mark(data: dict[str, Any]) -> Mark:
        raw_points = data["points"] if "points" in data else [data["position"]]
        return Mark(
            id=data["id"],
            kind=data["type"],
            points=tuple(GeoPoint.from_lat_lon(point) for point in raw_points),
            cross=data.get("cross"),
            leave_to=data.get("leave_to"),
        )

    @staticmethod
    def _build_finish(data: dict[str, Any]) -> Mark:
        points = tuple(GeoPoint.from_lat_lon(point) for point in data["line"])
        return Mark(id="finish", kind="line", points=points, cross=data.get("cross"))

    @staticmethod
    def _build_zone(data: dict[str, Any]) -> ExclusionZone:
        return ExclusionZone(
            id=data["id"],
            shape=data["shape"],
            points=tuple(GeoPoint.from_lat_lon(point) for point in data["points"]),
            kind=data.get("kind", "other"),
        )


def _parse_time(text: str) -> datetime:
    """ISO 8601 UTC time (`2026-11-01T12:02:00Z`) → aware datetime."""
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
