from datetime import UTC, datetime
from types import SimpleNamespace

import numpy as np

from sailrouter.domain.geo_point import GeoPoint
from sailrouter.routing.isochrone import Isochrone
from sailrouter.routing.isochrone_pruner import IsochronePruner


def _candidates(rng, n, legs):
    return Isochrone(
        time=datetime(2026, 11, 1, tzinfo=UTC), lat_deg=47 + rng.random(n), lon_deg=-5 + rng.random(n),
        parent=np.arange(n), heading_deg=np.zeros(n), twa_deg=np.zeros(n), tws_kn=np.zeros(n),
        sail=np.zeros(n, dtype=np.int8), speed_kn=np.zeros(n), leg=rng.integers(0, legs, n).astype(np.int16),
    )


def test_checking_obstacles_lazily_keeps_the_same_envelope_as_dropping_blocked_points_first():
    rng = np.random.default_rng(3)
    progress = SimpleNamespace(finished_leg=5, legs=[SimpleNamespace(anchor=GeoPoint(46.5, -6.0))] * 2)
    pruner = IsochronePruner(2.0)
    for _ in range(20):
        candidates = _candidates(rng, 400, legs=2)
        is_blocked = rng.random(400) < 0.6
        asked = []

        def blocked(indices, asked=asked, is_blocked=is_blocked):
            asked.extend(indices.tolist())
            return is_blocked[indices]

        lazy = pruner.prune(candidates, progress, blocked)
        eager = pruner.prune(candidates.subset(np.nonzero(~is_blocked)[0]), progress)
        assert np.array_equal(lazy.parent, eager.parent)
        assert len(asked) < 400 and len(set(asked)) == len(asked)


def test_every_candidate_blocked_gives_an_empty_front():
    rng = np.random.default_rng(1)
    progress = SimpleNamespace(finished_leg=5, legs=[SimpleNamespace(anchor=GeoPoint(46.5, -6.0))])
    front = IsochronePruner().prune(_candidates(rng, 50, legs=1), progress, lambda idx: np.ones(idx.size, bool))
    assert len(front) == 0
