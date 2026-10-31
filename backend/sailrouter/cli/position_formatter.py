from __future__ import annotations


class PositionFormatter:
    """Formats a position like the game shows it: `48°43'48"N 001°54'00"W`."""

    def format(self, lat_deg: float, lon_deg: float) -> str:
        return f"{self._dms(lat_deg, 'N', 'S', 2)} {self._dms(lon_deg, 'E', 'W', 3)}"

    @staticmethod
    def _dms(value: float, positive: str, negative: str, width: int) -> str:
        total_s = round(abs(value) * 3600)
        degrees, rest = divmod(total_s, 3600)
        minutes, seconds = divmod(rest, 60)
        letter = positive if value >= 0 else negative
        return f"{degrees:0{width}d}°{minutes:02d}'{seconds:02d}\"{letter}"
