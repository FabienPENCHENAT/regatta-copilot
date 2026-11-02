// Recognises the route the player has been following since the previous computation: the option of that
// computation whose route passes closest to the new position, and the rest of that route from there. The options
// share their first hours, so the one the player had selected wins a near tie, and the one the player picked
// by hand (`followedId`, when the position was entered too soon for the routes to part) always wins.

const FOLLOWED_WITHIN_NM = 30; // further from every route: the player made their own way
const TIE_NM = 5;
const EARTH_RADIUS_NM = 3440.065;

export class FollowedRouteFinder {
  // previous: { computedAt, selectedId, followedId, options: [{ id, path: [[lat, lon], ...] }] } (see RouteHistory).
  // Returns { optionId, computedAt, distanceNm, path, choices: [{ optionId, distanceNm }] } or null; `choices`
  // lists every option of that computation, for the player to pick another one.
  find(previous, position) {
    const all = previous.options.map((option) => ({ option, ...closestPoint(option.path, position) }))
      .filter((candidate) => candidate.index < candidate.option.path.length - 1); // something left to sail
    const near = all.filter((c) => c.distanceNm <= FOLLOWED_WITHIN_NM).sort((a, b) => a.distanceNm - b.distanceNm);
    const picked = all.find((c) => c.option.id === previous.followedId);
    const selected = near.find((c) => c.option.id === previous.selectedId);
    const chosen = picked ?? (selected && selected.distanceNm <= near[0].distanceNm + TIE_NM ? selected : near[0]);
    if (!chosen) return null;
    return {
      optionId: chosen.option.id, computedAt: previous.computedAt, distanceNm: chosen.distanceNm,
      path: chosen.option.path.slice(chosen.index + 1),
      choices: all.map((c) => ({ optionId: c.option.id, distanceNm: c.distanceNm })),
    };
  }
}

function closestPoint(path, position) {
  let best = { index: 0, distanceNm: Infinity };
  path.forEach(([lat, lon], index) => {
    const distanceNm = distanceBetween(position, { lat, lon });
    if (distanceNm < best.distanceNm) best = { index, distanceNm };
  });
  return best;
}

export function distanceBetween(a, b) {
  const rad = Math.PI / 180;
  const dLat = (b.lat - a.lat) * rad;
  const dLon = (b.lon - a.lon) * rad;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_RADIUS_NM * Math.asin(Math.sqrt(h));
}
