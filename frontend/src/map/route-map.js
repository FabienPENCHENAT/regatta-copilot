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
const VIEW_HOURS = { day: 24, near: 48, five: 120 }; // member paths hold one point per hour

export class RouteMap {
  #map;

  constructor(container, translator, { onSelectHour }) {
    // No zoom buttons: panels cover the corners; wheel, pinch and double-click zoom instead.
    this.#map = L.map(container, { zoomSnap: 0.5, minZoom: 3, maxZoom: 11, zoomControl: false });
    this.#map.setView([47, -5], 6);
    createPanes(this.#map);
    this.basemap = new ChartBasemap(this.#map, color);
    this.graticule = new GraticuleLayer(this.#map, color);
    this.seaLabels = new SeaLabels(this.#map, translator);
    this.course = new CourseLayer(this.#map, translator, color);
    this.routes = new RouteLayer(this.#map, translator, color, onSelectHour);
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

  showResult(result, option, hour) {
    this.routes.render(result, option, hour);
  }

  // "day" / "near": all scenario routes over the next 24 h / 48 h; "race": the whole ideal track to the finish.
  // insets = screen space covered by floating panels, in pixels, so the routes stay in the free area.
  fitView(result, view, insets) {
    const tracks = result.members.length ? result.members : result.options; // no members with a single forecast
    const points = view === "race" ? result.ideal_route.path : tracks.flatMap((t) => t.path.slice(0, VIEW_HOURS[view] + 1));
    this.#map.fitBounds(L.latLngBounds(points), {
      paddingTopLeft: [insets.left + 24, insets.top + 24],
      paddingBottomRight: [insets.right + 24, insets.bottom + 24],
    });
  }

  showBoat(option, hour, heading, startIso) {
    this.routes.showBoat(option, hour, heading, startIso);
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

  // Layers read the theme colours when they draw; the app redraws course, routes and wind right after.
  refreshTheme() {
    this.basemap.restyle();
    this.graticule.redraw();
    this.particles.hide();
  }
}
