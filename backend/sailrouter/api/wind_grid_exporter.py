from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np

from sailrouter.weather.wind_field import WindField

KN_TO_MS = 0.514444
MAP_BOX = {"south": 10.0, "north": 56.0, "west": -70.0, "east": 5.0, "step": 0.5}


class WindGridExporter:
    """Samples a `WindField` on the map grid at given hours, in the leaflet-velocity format the frontend
    draws (U record then V record, m/s, rows north to south)."""

    def export(self, wind: WindField, start: datetime, hours: list[int]) -> list[dict]:
        rows = np.arange(MAP_BOX["north"], MAP_BOX["south"] - 1e-9, -MAP_BOX["step"])
        cols = np.arange(MAP_BOX["west"], MAP_BOX["east"] + 1e-9, MAP_BOX["step"])
        lat, lon = np.meshgrid(rows, cols, indexing="ij")
        times = []
        for hour in hours:
            moment = start + timedelta(hours=hour)
            if not wind.first_time <= moment <= wind.last_time:
                continue
            tws_kn, twd_deg = wind.wind_at(lat.ravel(), lon.ravel(), moment.timestamp())
            speed = np.asarray(tws_kn) * KN_TO_MS
            towards = np.radians(np.asarray(twd_deg))
            u, v = -speed * np.sin(towards), -speed * np.cos(towards)
            times.append({"hour": hour, "grid": [self._record(2, u, rows, cols, moment), self._record(3, v, rows, cols, moment)]})
        return times

    @staticmethod
    def _record(parameter: int, values: np.ndarray, rows: np.ndarray, cols: np.ndarray, moment: datetime) -> dict:
        header = {
            "parameterCategory": 2, "parameterNumber": parameter, "nx": len(cols), "ny": len(rows),
            "lo1": float(cols[0]), "la1": float(rows[0]), "lo2": float(cols[-1]), "la2": float(rows[-1]),
            "dx": MAP_BOX["step"], "dy": MAP_BOX["step"], "refTime": moment.isoformat().replace("+00:00", "Z"),
        }
        return {"header": header, "data": [round(float(x), 1) for x in values]}
