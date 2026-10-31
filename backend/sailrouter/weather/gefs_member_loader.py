from __future__ import annotations

from collections.abc import Sequence

from sailrouter.weather.forecast_store import ForecastStore
from sailrouter.weather.grib_decoder import GribDecoder
from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.wind_field import WindField


class GefsMemberLoader:
    """Decodes the cached GRIB files of ONE GEFS member into its `WindField` (no download: the files must be
    in the store already, see `GefsRunDownloader`)."""

    def __init__(self, store: ForecastStore, decoder: GribDecoder) -> None:
        self._store = store
        self._decoder = decoder

    def wind_field(self, run: ModelRun, member: str, lead_hours: Sequence[int]) -> WindField:
        return WindField([self._decoder.decode(self._store.path(run, lead, member)) for lead in lead_hours])
