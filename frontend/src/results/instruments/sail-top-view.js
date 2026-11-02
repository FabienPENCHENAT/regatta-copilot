// The sail seen from above, as the game draws it on its compass: one curved stroke from the mast towards the
// stern, on the leeward side, eased with the wind angle (about half the TWA) and bellied by the wind. The same
// shape for every sail, in the boat's frame (bow up at y = -30, stern at y = 24, starboard = +x).

const MAST = { x: 0, y: -8 };
const LENGTH = 27;
const DEPTH = 0.16; // belly / length

export function sailTopViewPath(twaDeg) {
  if (twaDeg === null || twaDeg === undefined) return null;
  const twa = (twaDeg * Math.PI) / 180;
  const leeward = twaDeg >= 0 ? -1 : 1; // positive TWA: wind on starboard, sail to port
  const eased = (Math.min(Math.max(Math.abs(twaDeg) / 2, 6), 85) * Math.PI) / 180;
  const clew = { x: MAST.x + leeward * LENGTH * Math.sin(eased), y: MAST.y + LENGTH * Math.cos(eased) };
  // Belly pushed the way the wind blows (from bearing `twa` off the bow).
  const blows = { x: -Math.sin(twa), y: Math.cos(twa) };
  const dx = clew.x - MAST.x, dy = clew.y - MAST.y;
  let nx = -dy / LENGTH, ny = dx / LENGTH;
  if (nx * blows.x + ny * blows.y < 0) { nx = -nx; ny = -ny; }
  const control = { x: (MAST.x + clew.x) / 2 + nx * LENGTH * DEPTH * 2, y: (MAST.y + clew.y) / 2 + ny * LENGTH * DEPTH * 2 };
  return `M${MAST.x} ${MAST.y} Q${control.x.toFixed(1)} ${control.y.toFixed(1)} ${clew.x.toFixed(1)} ${clew.y.toFixed(1)}`;
}
