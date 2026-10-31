// The legs shown in the route plan and on the map (same list, same numbers): the orders of the next 48 h.

const PLAN_HORIZON_H = 48;

export function planLegs(option) {
  return option.legs.filter((leg) => leg.start_hour < PLAN_HORIZON_H);
}

// The leg being sailed at `hour` (the last one started at or before it).
export function legAt(legs, hour) {
  return legs.findLast((leg) => leg.start_hour <= hour);
}
