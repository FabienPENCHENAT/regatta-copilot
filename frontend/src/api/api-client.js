// Talks to the backend (FastAPI, same origin). Every method returns parsed JSON or throws an Error whose
// message is the server's explanation.

export class ApiClient {
  async listRaces() {
    return this.#get("/api/races");
  }

  async getRace(raceId) {
    return this.#get(`/api/races/${encodeURIComponent(raceId)}`);
  }

  async getPolar(raceId, boatId) {
    return this.#get(this.#polarUrl(raceId, boatId));
  }

  // request: { raceId, boatId, position: { lat, lon }, options, maneuvers, nextMark (null = automatic) }
  async computeRoute({ raceId, boatId, position, options, maneuvers, nextMark = null }) {
    return this.#send("/api/route", { race_id: raceId, boat_id: boatId, position, options, maneuvers, next_mark: nextMark });
  }

  // The player's polar exported from the game replaces the community copy for this race and boat.
  async importPolar({ raceId, boatId }, polar) {
    return this.#send(this.#polarUrl(raceId, boatId), polar);
  }

  async resetPolar({ raceId, boatId }) {
    return this.#parse(await fetch(this.#polarUrl(raceId, boatId), { method: "DELETE" }));
  }

  // Speed and best sail by TWA for some wind speeds and options: { twa: [...], curves: [{ tws, speed, sail }] }.
  async getPolarCurves({ raceId, boatId }, twsList, { sails = [], foil = false, hull = false } = {}) {
    const query = new URLSearchParams({ tws: twsList.join(","), sails: sails.join(","), foil, hull });
    return this.#get(`${this.#polarUrl(raceId, boatId)}/curves?${query}`);
  }

  // Miles gained on the game's route by going from `current` to `changed` options: { gains: [{ hours, gain_nm }] }.
  async compareOptions({ raceId, boatId, position, current, changed, maneuvers, nextMark = null }) {
    return this.#send("/api/options-impact", {
      race_id: raceId, boat_id: boatId, position, current, changed, maneuvers, next_mark: nextMark,
    });
  }

  #polarUrl(raceId, boatId) {
    return `/api/races/${encodeURIComponent(raceId)}/boats/${encodeURIComponent(boatId)}/polar`;
  }

  // Where the 31 GEFS scenarios stand: { state: "ready" | "downloading" | "unavailable", done, total, ... }.
  async getEnsembleStatus() {
    return this.#get("/api/ensemble/status");
  }

  // Newest weather on the server: { game_run: ISO | null, ensemble: { state, run, ... } }.
  async getLatestWeather() {
    return this.#get("/api/weather/latest");
  }

  // Map wind (the game's GFS) from the route start: the default hours, or the given ones (e.g. [11]).
  async getWindForecast(startIso, hours = null) {
    const query = hours ? `&hours=${hours.join(",")}` : "";
    return this.#get(`/api/wind?start=${encodeURIComponent(startIso)}${query}`);
  }

  async #get(url) {
    return this.#parse(await fetch(url));
  }

  async #send(url, body) {
    return this.#parse(await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }));
  }

  async #parse(response) {
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.detail ?? `HTTP ${response.status}`);
    return data;
  }
}
