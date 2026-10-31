from __future__ import annotations

import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable

GRIB_MAGIC = b"GRIB"


class DataNotAvailable(Exception):
    """NOMADS answered, but the requested file is not (yet) on the server."""


class NomadsClient:
    """Downloads one file through a NOMADS grib-filter script, politely.

    - HTTP/1.1 (urllib default): HTTP/2 requests hung against NOMADS in tests.
    - At most one request every `min_interval_s` (NOMADS bans clients that send too many requests per minute).
    - Retries network errors and 5xx/429 answers with exponential backoff; a 404 means "not available" at once.
    """

    BASE_URL = "https://nomads.ncep.noaa.gov/cgi-bin"

    def __init__(
        self,
        base_url: str = BASE_URL,
        min_interval_s: float = 1.0,
        max_attempts: int = 4,
        backoff_s: float = 2.0,
        timeout_s: float = 60.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._min_interval_s = min_interval_s
        self._max_attempts = max_attempts
        self._backoff_s = backoff_s
        self._timeout_s = timeout_s
        self._sleep = sleep
        self._last_request_at = 0.0

    def url(self, script: str, params: dict[str, str]) -> str:
        return f"{self._base_url}/{script}?{urllib.parse.urlencode(params)}"

    def fetch_grib(self, script: str, params: dict[str, str]) -> bytes:
        url = self.url(script, params)
        for attempt in range(1, self._max_attempts + 1):
            try:
                return self._fetch_once(url)
            except DataNotAvailable:
                raise
            except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                if attempt == self._max_attempts:
                    raise ConnectionError(f"NOMADS unreachable after {attempt} attempts: {error}") from error
                self._sleep(self._backoff_s * 2 ** (attempt - 1))
        raise AssertionError("unreachable")

    def _fetch_once(self, url: str) -> bytes:
        self._throttle()
        request = urllib.request.Request(url, headers={"User-Agent": "sailrouter/0.1 (VR routing advisor)"})
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_s) as response:
                body = response.read()
        except urllib.error.HTTPError as error:
            if error.code == 404:
                raise DataNotAvailable(url) from error
            raise
        if not body.startswith(GRIB_MAGIC):
            raise DataNotAvailable(f"{url}: answer is not GRIB ({body[:80]!r})")
        return body

    def _throttle(self) -> None:
        wait_s = self._last_request_at + self._min_interval_s - time.monotonic()
        if wait_s > 0:
            self._sleep(wait_s)
        self._last_request_at = time.monotonic()
