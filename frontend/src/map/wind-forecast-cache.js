// Map wind already loaded, by hour after the route start. The hour chips use the first batch (start, +4 h …);
// any other hour (e.g. a route-plan leg at +11 h) is fetched on demand and kept.

export class WindForecastCache {
  #start = null;
  #chipHours = [];
  #grids = new Map();
  #pending = new Map();

  constructor(api) {
    this.api = api;
  }

  reset(forecast) {
    this.#start = forecast.start;
    this.#chipHours = forecast.times.map((time) => time.hour);
    this.#grids = new Map(forecast.times.map((time) => [time.hour, time.grid]));
    this.#pending.clear();
  }

  get chipHours() {
    return this.#chipHours;
  }

  // The grid for `hour` if loaded, else the closest loaded hour before it (shown while the exact one loads).
  nearest(hour) {
    if (this.#grids.has(hour)) return { hour, grid: this.#grids.get(hour), exact: true };
    const before = [...this.#grids.keys()].filter((h) => h <= hour).sort((a, b) => b - a)[0] ?? this.#chipHours[0];
    return { hour: before, grid: this.#grids.get(before), exact: false };
  }

  // Loads the exact hour once; resolves to true when it is now available.
  async load(hour) {
    if (this.#grids.has(hour)) return true;
    if (!this.#pending.has(hour)) {
      const request = this.api.getWindForecast(this.#start, [hour]).then((forecast) => {
        for (const time of forecast.times) this.#grids.set(time.hour, time.grid);
        return this.#grids.has(hour);
      }).catch(() => false);
      this.#pending.set(hour, request);
    }
    return this.#pending.get(hour);
  }
}
