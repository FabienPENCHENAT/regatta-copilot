// Nautical-chart background drawn from vector data (no tile server needed):
// depth bands like a paper chart (shelf tinted blue, deep water paler) and buff land with a darker coastline.

const DEPTH_TOKENS = { 200: "--depth-200", 1000: "--depth-1000", 2000: "--depth-2000", 3000: "--depth-3000", 4000: "--depth-4000", 5000: "--depth-5000" };

export class ChartBasemap {
  constructor(map, colors) {
    this.map = map;
    this.color = colors;
  }

  async load({ depthsUrl, landUrl }) {
    const [depths, land] = await Promise.all([fetchJson(depthsUrl), fetchJson(landUrl)]);
    L.geoJSON(depths, {
      pane: "depths",
      interactive: false,
      style: (feature) => ({
        stroke: true, weight: 0.6, color: this.color("--depth-line"),
        fillColor: this.color(DEPTH_TOKENS[feature.properties.depth_m]), fillOpacity: 1,
      }),
    }).addTo(this.map);
    L.geoJSON(land, {
      pane: "land",
      interactive: false,
      attribution: "Natural Earth",
      style: () => ({ weight: 1, color: this.color("--coast"), fillColor: this.color("--land"), fillOpacity: 1 }),
    }).addTo(this.map);
  }
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Cannot load ${url}`);
  return response.json();
}
