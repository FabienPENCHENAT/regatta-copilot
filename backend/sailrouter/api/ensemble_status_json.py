from __future__ import annotations

from sailrouter.api.route_json_writer import iso
from sailrouter.service.ensemble_status import EnsembleStatus


def ensemble_status_json(status: EnsembleStatus) -> dict:
    """The `ensemble` object of a route result and of `GET /api/ensemble/status`."""
    return {
        "state": status.state,
        "run": iso(status.run.cycle) if status.run else None,
        "done": status.done,
        "total": status.total,
        "member_count": status.member_count,
    }
