// Animated wind particles (leaflet-velocity, loaded globally), coloured by wind strength.

import { WIND_COLOR_TOKENS, WIND_MAX_MS } from "./map-style.js";

export class WindParticlesLayer {
  #layer = null;

  constructor(map, colors) {
    this.map = map;
    this.color = colors;
  }

  show(gridRecords) {
    if (this.#layer) {
      this.#layer.setData(gridRecords);
      return;
    }
    this.#layer = L.velocityLayer({
      data: gridRecords,
      paneName: "wind",
      displayValues: false,
      minVelocity: 0,
      maxVelocity: WIND_MAX_MS,
      velocityScale: 0.007, // calm drift: the chart stays readable under the routes
      particleMultiplier: 1 / 640, // sparse particles (was 1 / 140, then 1 / 320)
      lineWidth: 2,
      opacity: 0.95,
      colorScale: WIND_COLOR_TOKENS.map((token) => this.color(token)),
    }).addTo(this.map);
  }

  hide() {
    if (!this.#layer) return;
    this.map.removeLayer(this.#layer);
    this.#layer = null;
  }
}
