from __future__ import annotations

import numpy as np

from sailrouter.polar.speed_model import SpeedModel

TWA_STEP_DEG = 2.0


class PolarCurves:
    """The polar as the router sees it for given options: boat speed and best sail every `TWA_STEP_DEG` from
    0 to 180°, for a few wind speeds (the polar page draws them)."""

    def __init__(self, speed_model: SpeedModel) -> None:
        self._speed = speed_model

    def at(self, tws_list: list[float]) -> dict:
        twa = np.arange(0.0, 180.0 + TWA_STEP_DEG / 2, TWA_STEP_DEG)
        names = self._speed.sail_names
        curves = []
        for tws in tws_list:
            sail, speed = self._speed.best(np.full(twa.shape, float(tws)), twa)
            curves.append({"tws": tws, "speed": [round(float(s), 3) for s in speed],
                           "sail": [names[int(i)] for i in sail]})
        return {"twa": [float(a) for a in twa], "curves": curves}
