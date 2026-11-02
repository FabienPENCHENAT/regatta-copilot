// The sail to hoist, seen from above, as one curved stroke in the boat's frame (bow up at y = -30, stern at
// y = 24): set on the leeward side and eased with the wind angle (about half the TWA). Not an exact drawing:
// headsails curve back from the bow, spinnakers and gennakers balloon ahead of it.

const HEADSAILS = { Jib: 0.16, LightJib: 0.16, Staysail: 0.14, Code0: 0.24 }; // camber (depth / chord)
const DOWNWIND = new Set(["Spi", "LightGnk", "HeavyGnk"]);

export function sailTopViewPath(sail, twaDeg) {
  if (!sail || twaDeg === null || twaDeg === undefined) return null;
  const leeward = twaDeg >= 0 ? -1 : 1; // positive TWA: wind on starboard, sail to port (negative x)
  const eased = (Math.min(Math.max(Math.abs(twaDeg) / 2, 8), 80) * Math.PI) / 180;
  return DOWNWIND.has(sail) ? balloon(sail, leeward, eased) : headsail(HEADSAILS[sail] ?? 0.16, sail, leeward, eased);
}

// Tack on the bow (the staysail inner forestay a little aft), clew aft to leeward, belly to leeward.
function headsail(camber, sail, leeward, eased) {
  const tack = { x: 0, y: sail === "Staysail" ? -20 : -28 };
  const chord = sail === "Staysail" ? 22 : 30;
  const clew = { x: leeward * chord * Math.sin(eased), y: tack.y + chord * Math.cos(eased) };
  return curve(tack, clew, chord * camber * 2, leeward, "aft");
}

// Spinnaker tacked on a pole to windward, gennakers on the bowsprit; clew far out to leeward; a deep bulge ahead.
function balloon(sail, leeward, eased) {
  const tack = sail === "Spi" ? { x: -leeward * 9, y: -34 } : { x: 0, y: -40 };
  const span = 44;
  const clew = { x: tack.x + leeward * span * Math.sin(eased), y: tack.y + span * Math.cos(eased) * 0.75 };
  return curve(tack, clew, span * 0.42, leeward, "ahead");
}

// Quadratic curve from a to b whose middle is pushed `depth` away from the chord, towards leeward and either
// aft (headsail belly) or ahead (spinnaker filling forward).
function curve(a, b, depth, leeward, side) {
  const mid = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
  const dx = b.x - a.x, dy = b.y - a.y, length = Math.hypot(dx, dy) || 1;
  let nx = -dy / length, ny = dx / length; // a normal of the chord
  const wanted = side === "ahead" ? ny < 0 : nx * leeward > 0; // ahead = towards the bow (negative y)
  if (!wanted) { nx = -nx; ny = -ny; }
  const control = { x: mid.x + nx * depth * 2, y: mid.y + ny * depth * 2 };
  return `M${a.x.toFixed(1)} ${a.y.toFixed(1)} Q${control.x.toFixed(1)} ${control.y.toFixed(1)} ${b.x.toFixed(1)} ${b.y.toFixed(1)}`;
}
