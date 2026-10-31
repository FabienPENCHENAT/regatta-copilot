from __future__ import annotations

from collections.abc import Callable

from sailrouter.weather.forecast_store import ForecastStore
from sailrouter.weather.gfs_query_builder import GfsQueryBuilder
from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.nomads_client import NomadsClient

ProgressCallback = Callable[[int, int], None]


class GfsRunDownloader:
    """Puts the requested lead times of one GFS run into the `ForecastStore`, downloading only missing ones.

    The last lead time is fetched first: if it is not on NOMADS yet, the run is incomplete and
    `DataNotAvailable` is raised before anything else is downloaded.
    """

    def __init__(self, client: NomadsClient, queries: GfsQueryBuilder, store: ForecastStore) -> None:
        self._client = client
        self._queries = queries
        self._store = store

    def download(self, run: ModelRun, lead_hours: list[int], on_progress: ProgressCallback | None = None) -> int:
        """Returns the number of files actually downloaded (0 when everything was cached)."""
        missing = [lead for lead in lead_hours if not self._store.has(run, lead)]
        if missing:
            missing = [missing[-1], *missing[:-1]]
        for done, lead in enumerate(missing, start=1):
            script, params = self._queries.query(run, lead)
            self._store.write(run, lead, self._client.fetch_grib(script, params))
            if on_progress:
                on_progress(done, len(missing))
        return len(missing)
