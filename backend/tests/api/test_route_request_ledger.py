from sailrouter.api.route_request_ledger import RouteRequestLedger


def test_a_newer_player_request_supersedes_older_ones_and_the_precomputation():
    ledger = RouteRequestLedger()
    first = ledger.staleness_check(new_request=True)
    background = ledger.staleness_check(new_request=False)
    assert not first() and not background()
    ledger.staleness_check(new_request=False)  # the precomputation never replaces anything
    assert not first() and not background()
    latest = ledger.staleness_check(new_request=True)
    assert first() and background() and not latest()
