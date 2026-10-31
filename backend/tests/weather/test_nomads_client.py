import io
import urllib.error

import pytest

from sailrouter.weather import nomads_client
from sailrouter.weather.nomads_client import DataNotAvailable, NomadsClient


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def fake_urlopen(answers, seen):
    def urlopen(request, timeout):
        seen.append(request.full_url)
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return FakeResponse(answer)

    return urlopen


def http_error(code):
    return urllib.error.HTTPError("https://x", code, "error", {}, io.BytesIO(b""))


def test_retries_server_errors_with_backoff(monkeypatch):
    seen, sleeps = [], []
    answers = [http_error(503), urllib.error.URLError("reset"), b"GRIB...7777"]
    monkeypatch.setattr(nomads_client.urllib.request, "urlopen", fake_urlopen(answers, seen))
    client = NomadsClient(min_interval_s=0.0, backoff_s=2.0, sleep=sleeps.append)
    assert client.fetch_grib("filter_gfs_0p25.pl", {"file": "gfs.t06z.pgrb2.0p25.f000"}) == b"GRIB...7777"
    assert len(seen) == 3
    assert sleeps == [2.0, 4.0]
    assert "filter_gfs_0p25.pl?file=gfs.t06z.pgrb2.0p25.f000" in seen[0]


def test_missing_file_is_not_retried(monkeypatch):
    seen = []
    monkeypatch.setattr(nomads_client.urllib.request, "urlopen", fake_urlopen([http_error(404)], seen))
    with pytest.raises(DataNotAvailable):
        NomadsClient(min_interval_s=0.0, sleep=lambda s: None).fetch_grib("f.pl", {})
    assert len(seen) == 1


def test_html_answer_means_not_available(monkeypatch):
    answers = [b"<html>data file is not present</html>"]
    monkeypatch.setattr(nomads_client.urllib.request, "urlopen", fake_urlopen(answers, []))
    with pytest.raises(DataNotAvailable):
        NomadsClient(min_interval_s=0.0, sleep=lambda s: None).fetch_grib("f.pl", {})


def test_gives_up_after_max_attempts(monkeypatch):
    answers = [urllib.error.URLError("down")] * 3
    monkeypatch.setattr(nomads_client.urllib.request, "urlopen", fake_urlopen(answers, []))
    with pytest.raises(ConnectionError):
        NomadsClient(min_interval_s=0.0, max_attempts=3, sleep=lambda s: None).fetch_grib("f.pl", {})
