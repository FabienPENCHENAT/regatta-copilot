// Stand-in for the backend API during the mock-up step. Same interface as the future ApiClient:
// listRaces(), getRace(id), getWindForecast(), computeRoute(request, onProgress).

const RACES = [
  {
    id: "route-du-rhum-2026",
    boats: ["class40", "imoca", "ocean_fifty", "ultim", "vintage_multi"],
    default_boat: "class40",
  },
];
const SCENARIO_COUNT = 31;

export class MockApi {
  async listRaces() {
    return RACES;
  }

  async getRace(raceId) {
    return fetchJson(`mock/races/${raceId}.json`);
  }

  // Real GFS wind (the game's weather) at the start and at each route-plan hour.
  async getWindForecast() {
    return fetchJson("mock/wind-forecast.json");
  }

  async computeRoute(request, onProgress) {
    for (let done = 1; done <= SCENARIO_COUNT; done += 1) {
      await delay(40);
      onProgress(done, SCENARIO_COUNT);
    }
    return this.loadSample();
  }

  async loadSample() {
    return fetchJson("mock/sample-result.json");
  }
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Cannot load ${url}`);
  return response.json();
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
