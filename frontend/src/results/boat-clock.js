// Where the boat should be now on the shown route: the hours elapsed since the route's start (the time its
// position was computed for), so the boat moves along its line with the clock. Calls `onTick` every minute.

const TICK_MS = 60_000;
const MS_PER_HOUR = 3_600_000;

export class BoatClock {
  #timer = null;

  constructor(onTick, now = () => Date.now()) {
    this.onTick = onTick;
    this.now = now;
  }

  start() {
    clearInterval(this.#timer);
    this.#timer = setInterval(() => this.onTick(), TICK_MS);
  }

  // Hours since `startIso`, between 0 and `maxHour` (the end of the route).
  hoursSince(startIso, maxHour) {
    const hours = (this.now() - Date.parse(startIso)) / MS_PER_HOUR;
    return Math.min(Math.max(hours, 0), maxHour);
  }
}
