// Nautical-chart background drawn from vector data (no tile server needed):
// depth bands (deeper = darker) and pale land with a thin coastline. Restyled when the theme changes.

const DEPTH_TOKENS = { 200: "--depth-200", 1000: "--depth-1000", 2000: "--depth-2000", 3000: "--depth-3000", 4000: "--depth-4000", 5000: "--depth-5000" };

export class ChartBasemap {
  #depths = null;
  #land = null;

  constructor(map, colors) {
    this.map = map;
    this.color = colors;
  }

  async load({ depthsUrl, landUrl }) {
    const [depths, land] = await Promise.all([fetchJson(depthsUrl), fetchJson(landUrl)]);
    this.#depths = L.geoJSON(depths, { pane: "depths", interactive: false, style: (f) => this.#depthStyle(f) }).addTo(this.map);
    this.#land = L.geoJSON(land, { pane: "land", interactive: false, attribution: "Natural Earth", style: () => this.#landStyle() })
      .addTo(this.map);
  }

  restyle() {
    this.#depths?.setStyle((f) => this.#depthStyle(f));
    this.#land?.setStyle(() => this.#landStyle());
  }

  #depthStyle(feature) {
    return {
      stroke: true, weight: 0.6, color: this.color("--depth-line"),
      fillColor: this.color(DEPTH_TOKENS[feature.properties.depth_m]), fillOpacity: 1,
    };
  }

  #landStyle() {
    return { weight: 1, color: this.color("--coast"), fillColor: this.color("--land"), fillOpacity: 1 };
  }
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Cannot load ${url}`);
  return response.json();
}
