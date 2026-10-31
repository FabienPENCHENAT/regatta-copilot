from __future__ import annotations

import math
import re

from sailrouter.domain.geo_point import GeoPoint

# Twin of frontend/src/form/position-parser.js: keep both behaviours identical.
# Accepted forms: 47°30'00"N 006°45'00"W   47°30.5'N 6°45.2'W   47.5N 6.75W   47.5, -6.75   47,5 ; -6,75
# "O" (ouest) is accepted for west.
_NUMBER = r"([0-9]+(?:[.,][0-9]+)?)"
_HEMISPHERE_PART = re.compile(
    rf"{_NUMBER}\s*°?\s*(?:{_NUMBER}\s*['′’]\s*)?(?:{_NUMBER}\s*(?:[\"″”]|''))?\s*([NSEWO])",
    re.IGNORECASE,
)
_SIGNED_DOT_PAIR = re.compile(r"\s*(-?[0-9]+(?:\.[0-9]+)?)\s*[,;\s]\s*(-?[0-9]+(?:\.[0-9]+)?)\s*")
_SIGNED_COMMA_PAIR = re.compile(r"\s*(-?[0-9]+(?:,[0-9]+)?)\s*[;\s]\s*(-?[0-9]+(?:,[0-9]+)?)\s*")


class PositionParser:
    """Turns a position typed or pasted by the user into a `GeoPoint`, or `None` if it is not understood."""

    def parse(self, text: str | None) -> GeoPoint | None:
        if not text or not text.strip():
            return None
        position = self._parse_hemispheres(text) or self._parse_signed_pair(text)
        if position is None or not self._is_valid(*position):
            return None
        return GeoPoint(*position)

    def _parse_hemispheres(self, text: str) -> tuple[float, float] | None:
        parts = _HEMISPHERE_PART.findall(text)
        if len(parts) != 2:
            return None
        lat: float | None = None
        lon: float | None = None
        for deg, minutes, seconds, letter in parts:
            value = _to_number(deg) + _to_number(minutes) / 60 + _to_number(seconds) / 3600
            hemisphere = letter.upper()
            if hemisphere in ("N", "S"):
                lat = -value if hemisphere == "S" else value
            else:
                lon = value if hemisphere == "E" else -value
        return (lat, lon) if lat is not None and lon is not None else None

    def _parse_signed_pair(self, text: str) -> tuple[float, float] | None:
        match = _SIGNED_DOT_PAIR.fullmatch(text) or _SIGNED_COMMA_PAIR.fullmatch(text)
        return (_to_number(match[1]), _to_number(match[2])) if match else None

    @staticmethod
    def _is_valid(lat: float, lon: float) -> bool:
        return math.isfinite(lat) and math.isfinite(lon) and abs(lat) <= 90 and abs(lon) <= 180


def _to_number(text: str) -> float:
    return float(text.replace(",", ".", 1)) if text else 0.0
