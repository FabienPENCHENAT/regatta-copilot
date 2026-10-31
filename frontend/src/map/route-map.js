// The chart: builds the Leaflet map and its layers, and exposes what the app needs
// (course, result, selected option and hour, wind display mode). Each layer does its own drawing.

import { ChartBasemap } from "./chart-basemap.js";
import { CourseLayer } from "./course-layer.js";
import { GraticuleLayer } from "./graticule-layer.js";
import { RouteLayer } from "./route-layer.js";
import { SeaLabels } from "./sea-labels.js";
import { WindBarbsLayer } from "./wind-barbs-layer.js";
import { WindGrid } from "./wind-grid.js";
import { WindParticlesLayer } from "./wind-particles-layer.js";
import { color, createPanes } from "./map-style.js";

export const WIND_MODES = ["particles", "barbs"];

export class RouteMap {
  #map;

  constructor(container, translator) {
    this.#map = L.map(container, { zoomSnap: 0.5, minZoom: 3, maxZoom: 11, zoomControl: false });
    L.control.zoom({ position: "topright" }).addTo(this.#map);
    this.#map.setView([47, -5], 6);
    createPanes(this.#map);
    this.basemap = new ChartBasemap(this.#map, color);
    this.graticule = new GraticuleLayer(this.#map, color);
    this.seaLabels = new SeaLabels(this.#map, translator);
    this.course = new CourseLayer(this.#map, translator, color);
    this.routes = new RouteLayer(this.#map, translator, color);
    this.particles = new WindParticlesLayer(this.#map, color);
    this.barbs = new WindBarbsLayer(this.#map, color);
  }

  async loadBasemap(urls) {
    await this.basemap.load(urls);
    this.graticule.redraw();
    this.seaLabels.render();
  }

  showCourse(race, boatId) {
    this.course.render(race, boatId);
  }

  showResult(result, option) {
    this.routes.render(result, option);
  }

  // "near": the next 48 h (all scenario routes); "race": the whole ideal track to the finish.
  fitView(result, view) {
    const points = view === "race" ? result.ideal_route.path : result.members.flatMap((m) => m.path);
    this.#map.fitBounds(L.latLngBounds(points), { padding: [20, 20] });
  }

  showBoat(option, hour, heading) {
    this.routes.showBoat(option, hour, heading);
  }

  showPosition(position) {
    if (position) this.#map.panTo([position.lat, position.lon]);
  }

  showWind(gridRecords, mode) {
    if (mode === "particles") {
      this.barbs.hide();
      this.particles.show(gridRecords);
    } else {
      this.particles.hide();
      this.barbs.show(new WindGrid(gridRecords));
    }
  }

  retranslate() {
    this.seaLabels.render();
  }
}
