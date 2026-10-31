from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import eccodes
import numpy as np

from sailrouter.weather.wind_grid import WindGrid

U_NAME, V_NAME = "10u", "10v"


class GribDecoder:
    """Reads a GRIB2 file holding the 10 m U and V wind messages into a `WindGrid` (via ecCodes)."""

    def decode(self, path: Path) -> WindGrid:
        messages = self._read_messages(path)
        missing = {U_NAME, V_NAME} - messages.keys()
        if missing:
            raise ValueError(f"{path.name}: missing GRIB messages {sorted(missing)}")
        u_meta, u_values = messages[U_NAME]
        v_meta, v_values = messages[V_NAME]
        same_grid = all(np.array_equal(a, b) for a, b in zip(u_meta[:2], v_meta[:2])) and u_meta[2:] == v_meta[2:]
        if not same_grid:
            raise ValueError(f"{path.name}: U and V grids differ")
        lat, lon, valid_time, scans_north = u_meta
        if not scans_north:
            u_values, v_values = u_values[::-1], v_values[::-1]
        return WindGrid(valid_time, lat, lon, u_values, v_values)

    def _read_messages(self, path: Path) -> dict[str, tuple[tuple, np.ndarray]]:
        messages: dict[str, tuple[tuple, np.ndarray]] = {}
        with path.open("rb") as stream:
            while (handle := eccodes.codes_grib_new_from_file(stream)) is not None:
                try:
                    name = eccodes.codes_get(handle, "shortName")
                    meta = self._grid_meta(handle)
                    shape = (meta[0].size, meta[1].size)
                    values = eccodes.codes_get_values(handle).astype(np.float32).reshape(shape)
                    messages[name] = (meta, values)
                finally:
                    eccodes.codes_release(handle)
        return messages

    @staticmethod
    def _grid_meta(handle: int) -> tuple:
        if eccodes.codes_get(handle, "iScansNegatively"):
            raise ValueError("GRIB grids scanning westward are not supported")
        ni, nj = eccodes.codes_get(handle, "Ni"), eccodes.codes_get(handle, "Nj")
        di = eccodes.codes_get(handle, "iDirectionIncrementInDegrees")
        dj = eccodes.codes_get(handle, "jDirectionIncrementInDegrees")
        lat_first = eccodes.codes_get(handle, "latitudeOfFirstGridPointInDegrees")
        lat_last = eccodes.codes_get(handle, "latitudeOfLastGridPointInDegrees")
        lon_first = (eccodes.codes_get(handle, "longitudeOfFirstGridPointInDegrees") + 180.0) % 360.0 - 180.0
        scans_north = bool(eccodes.codes_get(handle, "jScansPositively"))
        lat_south = lat_first if scans_north else lat_last
        lat = np.round(lat_south + dj * np.arange(nj), 6)
        lon = np.round(lon_first + di * np.arange(ni), 6)
        if lon[-1] >= 180.0:
            raise ValueError("GRIB grids crossing the antimeridian are not supported")
        valid = datetime.strptime(
            f"{eccodes.codes_get(handle, 'validityDate')}{eccodes.codes_get(handle, 'validityTime'):04d}",
            "%Y%m%d%H%M",
        ).replace(tzinfo=UTC)
        return lat, lon, valid, scans_north
