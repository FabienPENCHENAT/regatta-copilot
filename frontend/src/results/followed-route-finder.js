// Recognises the route the player has been following since the previous computation: the option of that
// computation whose route passes closest to the new position, and the rest of that route from there. The options
// share their first hours, so the one the player had selected wins a near tie.

const FOLLOWED_WITHIN_NM = 30; // further from every route: the player made their own way
const TIE_NM = 5;
const EARTH_RADIUS_NM = 3440.065;

export class FollowedRouteFinder {
  // previous: { computedAt, selectedId, options: [{ id, path: [[lat, lon], ...] }] } (see RouteHistory).
  // Returns { optionId, computedAt, distanceNm, path } or null.
  find(previous, position) {
    const candidates = previous.options
      .map((option) => ({ option, ...closestPoint(option.path, position) }))
      .filter((candidate) => candidate.distanceNm <= FOLLOWED_WITHIN_NM)
      .sort((a, b) => a.distanceNm - b.distanceNm);
    if (!candidates.length) return null;
    const selected = candidates.find((c) => c.option.id === previous.selectedId);
    const chosen = selected && selected.distanceNm <= candidates[0].distanceNm + TIE_NM ? selected : candidates[0];
    const path = chosen.option.path.slice(chosen.index + 1);
    if (!path.length) return null;
    return { optionId: chosen.option.id, computedAt: previous.computedAt, distanceNm: chosen.distanceNm, path };
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
