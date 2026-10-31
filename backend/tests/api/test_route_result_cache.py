from datetime import UTC, datetime, timedelta

from sailrouter.api.route_result_cache import RouteResultCache


def test_same_inputs_give_the_same_key_whatever_the_order():
    assert RouteResultCache.key({"a": 1, "b": [1, 2]}) == RouteResultCache.key({"b": [1, 2], "a": 1})
    assert RouteResultCache.key({"gfs": "gfs-2026103106"}) != RouteResultCache.key({"gfs": "gfs-2026103112"})


def test_stored_result_comes_back_until_it_expires(tmp_path):
    cache = RouteResultCache(tmp_path)
    now = datetime(2026, 11, 1, 12, tzinfo=UTC)
    cache.put("forever", {"x": 1})
    cache.put("soon", {"y": 2}, expires_at=now + timedelta(minutes=30))
    assert cache.get("forever", now) == {"x": 1}
    assert cache.get("soon", now) == {"y": 2}
    assert cache.get("soon", now + timedelta(minutes=31)) is None
    assert cache.get("missing", now) is None
