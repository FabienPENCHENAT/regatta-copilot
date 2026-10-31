from __future__ import annotations

from sailrouter.ensemble.route_option import RouteOption

ADVICE_HOURS = 48


class AdviceWriter:
    """The headline advice as an i18n key and its parameters (the frontend writes the sentence, decision D7)."""

    def advice(self, options: list[RouteOption], member_total: int) -> dict:
        best = options[0]
        if len(options) == 1:
            return {"key": "advice.consensus",
                    "params": {"count": len(best.members), "total": member_total, "hours": ADVICE_HOURS}}
        return {"key": "advice.head_direction",
                "params": {"option": best.id, "count": len(best.members), "total": member_total,
                           "hours": ADVICE_HOURS}}
