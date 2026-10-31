from __future__ import annotations

from collections.abc import Callable, Sequence

from sailrouter.weather.forecast_store import ForecastStore
from sailrouter.weather.gefs_query_builder import GefsQueryBuilder
from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.nomads_client import NomadsClient

ProgressCallback = Callable[[int, int], None]


class GefsRunDownloader:
    """Puts the requested lead times of every GEFS member into the `ForecastStore`, downloading only missing files.

    The last lead time of every member is fetched first: a run is complete only when all members reached it,
    so an incomplete run raises `DataNotAvailable` within the first requests. Progress counts files on disk
    (cached ones included) out of the total, so a resumed download starts where it stopped.
    """

    def __init__(self, client: NomadsClient, queries: GefsQueryBuilder, store: ForecastStore) -> None:
        self._client = client
        self._queries = queries
        self._store = store

    def download(
        self, run: ModelRun, lead_hours: Sequence[int], members: Sequence[str],
        on_progress: ProgressCallback | None = None,
    ) -> int:
        """Returns the number of files actually downloaded (0 when everything was cached)."""
        total = len(lead_hours) * len(members)
        missing = self._store.missing(run, lead_hours, members)
        last = max(lead_hours)
        missing.sort(key=lambda item: item[0] != last)  # stable sort: completeness probes first
        done = total - len(missing)
        if on_progress:
            on_progress(done, total)
        for lead, member in missing:
            script, params = self._queries.query(run, lead, member)
            self._store.write(run, lead, self._client.fetch_grib(script, params), member)
            done += 1
            if on_progress:
                on_progress(done, total)
        return len(missing)
