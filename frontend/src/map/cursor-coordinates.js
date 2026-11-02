// Position under the mouse, shown at the top centre of the page in the same format as the race card, so it can
// be compared with the coordinates the game shows under its own cursor. Mouse only: hidden on touch screens
// and whenever the pointer leaves the chart.

import { formatCoordinates } from "../results/display-format.js";

export class CursorCoordinates {
  constructor(map, element) {
    this.element = element;
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    map.on("mousemove", (event) => this.#show(event.latlng));
    map.on("mouseout", () => { this.element.hidden = true; });
  }

  #show({ lat, lng }) {
    const lon = ((((lng + 180) % 360) + 360) % 360) - 180; // the chart may be panned past the antimeridian
    this.element.textContent = formatCoordinates({ lat, lon });
    this.element.hidden = false;
  }
}
