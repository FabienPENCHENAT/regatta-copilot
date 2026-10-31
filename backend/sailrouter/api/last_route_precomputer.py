from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from time import perf_counter

from sailrouter.api.cached_route_computer import CachedRouteComputer
from sailrouter.api.last_route_request_store import LastRouteRequestStore
from sailrouter.course.race_catalog import RaceCatalog

KEEP_WARM_FOR = timedelta(hours=6)  # recent request: also recompute when its 30-min start slot changes
log = logging.getLogger(__name__)


class LastRoutePrecomputer:
    """Computes the last route request again in the background, so reopening the site answers instantly.

    Always when the weather changed; otherwise only while the request is recent (`KEEP_WARM_FOR`), since a race
    under way rounds its start to 30 min and the stored result goes stale (a cached result costs nothing)."""

    def __init__(self, store: LastRouteRequestStore, computer: CachedRouteComputer, catalog: RaceCatalog,
                 now: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None:
        self._store = store
        self._computer = computer
        self._catalog = catalog
        self._now = now

    def window(self, now: datetime) -> tuple[datetime, datetime] | None:
        """Route window of the last request's race (or of the first race known), for the weather downloads."""
        last = self._store.load()
        race_ids = [last[0].race_id] if last else self._catalog.race_ids()[:1]
        if not race_ids:
            return None
        return self._computer.window(self._catalog.load(race_ids[0]), now)

    def precompute(self, weather_changed: bool) -> bool:
        """Whether the last request was (re)computed or read back from the result cache."""
        last = self._store.load()
        if last is None:
            log.info("no route request received yet: nothing to pre-compute")
            return False
        request, received_at = last
        if not weather_changed and self._now() - received_at > KEEP_WARM_FOR:
            return False
        began = perf_counter()
        self._computer.result(request)
        log.info("pre-computed the last route request (%s/%s at %.4f, %.4f) in %.1f s", request.race_id,
                 request.boat_id, request.position.lat, request.position.lon, perf_counter() - began)
        return True
