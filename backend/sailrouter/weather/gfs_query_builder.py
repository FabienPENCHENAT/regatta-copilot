from __future__ import annotations

from datetime import UTC

from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.weather_area import WeatherArea


class GfsQueryBuilder:
    """Builds the NOMADS grib-filter query (script + parameters) for one deterministic GFS 0.25° lead time.

    Only the 10 m wind (UGRD, VGRD) over `area` is requested (≈ 280 KB per lead time for 0–60°N / 80°W–10°E).
    A `GefsQueryBuilder` with a member number will follow the same interface in step 4.
    """

    SCRIPT = "filter_gfs_0p25.pl"

    def __init__(self, area: WeatherArea) -> None:
        self._area = area

    def query(self, run: ModelRun, lead_h: int) -> tuple[str, dict[str, str]]:
        cycle = run.cycle.astimezone(UTC)
        params = {
            "dir": f"/gfs.{cycle:%Y%m%d}/{cycle:%H}/atmos",
            "file": f"gfs.t{cycle:%H}z.pgrb2.0p25.f{lead_h:03d}",
            "var_UGRD": "on",
            "var_VGRD": "on",
            "lev_10_m_above_ground": "on",
            "subregion": "",
            "toplat": _fmt(self._area.north_deg),
            "leftlon": _fmt(self._area.west_deg),
            "rightlon": _fmt(self._area.east_deg),
            "bottomlat": _fmt(self._area.south_deg),
        }
        return self.SCRIPT, params


def _fmt(value: float) -> str:
    return f"{value:g}"
