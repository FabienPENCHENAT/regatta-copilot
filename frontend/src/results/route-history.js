// Remembers, in the browser, the options of the latest computation and of the one made from the previous
// position, so a new computation from a new position can tell which route the player has been following.
// Recomputing from the same position (new forecast, other settings) keeps the earlier reference.

import { distanceBetween } from "./followed-route-finder.js";

const MOVED_NM = 3; // closer: the same position, recomputed

export class RouteHistory {
  constructor(preferences) {
    this.preferences = preferences;
  }

  // The computation to compare a new one with: the latest if the boat has moved since, else the one before.
  previousFor({ raceId, boatId, position }) {
    const { latest, earlier } = this.preferences.read().routeHistory ?? {};
    const reference = latest && moved(latest, position) ? latest : earlier;
    return reference && reference.raceId === raceId && reference.boatId === boatId ? reference : null;
  }

  remember(result, selectedId) {
    const { latest, earlier } = this.preferences.read().routeHistory ?? {};
    const entry = {
      raceId: result.race_id, boatId: result.boat_id, position: result.position, computedAt: result.computed_at,
      selectedId,
      options: result.options.map((option) => ({ id: option.id, path: option.path })),
    };
    this.preferences.update({ routeHistory: { latest: entry, earlier: latest && moved(latest, result.position) ? latest : earlier } });
  }

  // The option the player looks at is the one they are likely to follow.
  select(optionId) {
    const history = this.preferences.read().routeHistory;
    if (!history?.latest) return;
    this.preferences.update({ routeHistory: { ...history, latest: { ...history.latest, selectedId: optionId } } });
  }
}

function moved(entry, position) {
  return distanceBetween(entry.position, position) > MOVED_NM;
}
