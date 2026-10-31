// Stand-in for the backend API during the mock-up step. Same interface as the future ApiClient:
// listRaces() and computeRoute(request, onProgress). Returns a fixed example result.

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

  async computeRoute(request, onProgress) {
    for (let done = 1; done <= SCENARIO_COUNT; done += 1) {
      await delay(40);
      onProgress(done, SCENARIO_COUNT);
    }
    return this.loadSample();
  }

  async loadSample() {
    const response = await fetch("mock/sample-result.json");
    return response.json();
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
