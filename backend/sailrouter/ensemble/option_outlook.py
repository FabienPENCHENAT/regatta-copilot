from __future__ import annotations

import numpy as np


class OptionOutlook:
    """Sums up the cross-evaluation (each track sailed in every member's weather) against a reference track (the
    player's current route, else the recommended option), at each hour measured: mean distance to go (through
    every remaining mark), mean and worst gain over the reference (nm, positive = ahead) and the share of
    scenarios where it is ahead. Distances to go are comparable between tracks, not with an option's own route
    (sailed in one weather)."""

    def summarize(self, outlook: list[dict[str, dict[float, float]]],
                  reference: dict[str, dict[float, float]] | None = None) -> list[list[dict]]:
        """`reference`: {member: {hour: distance to go}} of the reference track; default: the first one."""
        if not outlook or not outlook[0]:
            return [[] for _ in outlook]
        reference = reference or outlook[0]
        members = sorted(outlook[0])
        hours = sorted(next(iter(outlook[0].values())))
        summaries = []
        for per_member in outlook:
            rows = []
            for hour in hours:
                to_go = np.array([per_member[m][hour] for m in members])
                gain = np.array([reference[m][hour] for m in members]) - to_go
                rows.append({"hours": int(round(hour)), "to_go_nm": round(float(to_go.mean())),
                             "gain_nm": round(float(gain.mean()), 1), "worst_nm": round(float(gain.min()), 1),
                             "ahead_share": round(float((gain > 0.5).mean()), 2)})
            summaries.append(rows)
        return summaries
