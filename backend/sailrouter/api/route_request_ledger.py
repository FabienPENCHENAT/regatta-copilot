from __future__ import annotations

import threading
from collections.abc import Callable


class RouteRequestLedger:
    """Numbers the player's route requests, so a computation waiting or running for an older one can tell it
    has been replaced and stop: changing three settings in a row must not cost three full computations."""

    def __init__(self) -> None:
        self._latest = 0
        self._lock = threading.Lock()

    def staleness_check(self, new_request: bool) -> Callable[[], bool]:
        """A check telling whether a newer request arrived after this one. `new_request` is False for the
        background pre-computation: it never replaces the player's requests, only yields to them."""
        with self._lock:
            if new_request:
                self._latest += 1
            ticket = self._latest
        return lambda: self._latest > ticket
