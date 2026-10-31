// Beaufort force from a wind speed in knots (upper bound of each force, WMO table).

const UPPER_KNOTS = [1, 3, 6, 10, 16, 21, 27, 33, 40, 47, 55, 63];

export function beaufortForce(speedKn) {
  const force = UPPER_KNOTS.findIndex((upper) => speedKn < upper + 0.5);
  return force === -1 ? 12 : force;
}
