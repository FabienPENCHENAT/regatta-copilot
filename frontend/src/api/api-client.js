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
    return this.#get(`/api/races/${encodeURIComponent(raceId)}/boats/${encodeURIComponent(boatId)}/polar`);
  }

  // request: { raceId, boatId, position: { lat, lon }, options: { sails, foil, hull, pro_winch } }
  async computeRoute({ raceId, boatId, position, options }) {
    return this.#send("/api/route", { race_id: raceId, boat_id: boatId, position, options });
  }

  // Map wind (the game's GFS) at the start and at each route-plan hour.
  async getWindForecast(startIso) {
    return this.#get(`/api/wind?start=${encodeURIComponent(startIso)}`);
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
