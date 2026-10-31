// One "Compute my route": asks the backend for the route, then for the map wind from the route's start.

export class RouteComputation {
  constructor(api) {
    this.api = api;
  }

  async run(request) {
    const result = await this.api.computeRoute(request);
    const wind = await this.api.getWindForecast(result.computed_at);
    return { result, wind };
  }
}
