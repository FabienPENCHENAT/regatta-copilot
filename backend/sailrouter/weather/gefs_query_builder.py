from __future__ import annotations

from datetime import UTC

from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.weather_area import WeatherArea

# Control member then the 30 perturbed members, as named in the NOMADS file names (gec00, gep01..gep30).
GEFS_MEMBERS = ("c00", *(f"p{n:02d}" for n in range(1, 31)))


class GefsQueryBuilder:
    """Builds the NOMADS grib-filter query (script + parameters) for one GEFS 0.5° member and lead time.

    Same parameters as `GfsQueryBuilder` plus the member (`c00`, `p01`..`p30`). Only the 10 m wind (UGRD, VGRD)
    over `area` is requested (≈ 66 KB per file for 0–60°N / 80°W–10°E).
    """

    SCRIPT = "filter_gefs_atmos_0p50a.pl"

    def __init__(self, area: WeatherArea) -> None:
        self._area = area

    def query(self, run: ModelRun, lead_h: int, member: str) -> tuple[str, dict[str, str]]:
        if member not in GEFS_MEMBERS:
            raise ValueError(f"unknown GEFS member {member!r}")
        cycle = run.cycle.astimezone(UTC)
        params = {
            "dir": f"/gefs.{cycle:%Y%m%d}/{cycle:%H}/atmos/pgrb2ap5",
            "file": f"ge{member}.t{cycle:%H}z.pgrb2a.0p50.f{lead_h:03d}",
            "var_UGRD": "on",
            "var_VGRD": "on",
            "lev_10_m_above_ground": "on",
            "subregion": "",
            "toplat": f"{self._area.north_deg:g}",
            "leftlon": f"{self._area.west_deg:g}",
            "rightlon": f"{self._area.east_deg:g}",
            "bottomlat": f"{self._area.south_deg:g}",
        }
        return self.SCRIPT, params
