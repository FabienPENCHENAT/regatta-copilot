// Tells when the server holds newer weather than the shown result was computed on: a newer GFS run (the game's
// weather) or newer GEFS scenarios. Asks every few minutes and whenever `check` is called; `onNewer` is called
// once per result.

const CHECK_EVERY_MS = 5 * 60 * 1000;

export class WeatherUpdateCheck {
  #result = null;
  #timer = null;

  constructor(api, onNewer) {
    this.api = api;
    this.onNewer = onNewer;
  }

  watch(result) {
    this.#result = result;
    clearInterval(this.#timer);
    this.#timer = setInterval(() => this.check(), CHECK_EVERY_MS);
    this.check();
  }

  async check() {
    const result = this.#result;
    if (!result) return;
    const latest = await this.api.getLatestWeather().catch(() => null);
    if (!latest || result !== this.#result || !isNewer(latest, result.weather)) return;
    this.#result = null;
    clearInterval(this.#timer);
    this.onNewer();
  }
}

// weather: the result's `weather`; its game run is `game_run`, or `run` when only the GFS was routed.
function isNewer(latest, weather) {
  const scenarios = weather.member_count > 1;
  const gameRun = scenarios ? weather.game_run : weather.run;
  const newerGame = latest.game_run && Date.parse(latest.game_run) > Date.parse(gameRun);
  const ensemble = latest.ensemble;
  const newerScenarios = ensemble?.state === "ready" && ensemble.run
    && (!scenarios || Date.parse(ensemble.run) > Date.parse(weather.run));
  return Boolean(newerGame || newerScenarios);
}
