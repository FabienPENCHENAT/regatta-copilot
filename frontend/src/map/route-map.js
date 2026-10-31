// Leaflet map: my position, the 31 scenario routes (thin), the selected option (thick)
// and its target areas at each horizon, coloured by confidence.

import { addBasemap } from "./basemap.js";
import { confidenceLevel } from "../results/display-format.js";

const NM_IN_METERS = 1852;

export class RouteMap {
  #map;
  #positionLayer;
  #resultLayer;

  constructor(container, translator) {
    this.translator = translator;
    this.#map = L.map(container, { worldCopyJump: true, zoomSnap: 0.5 }).setView([44, -12], 5);
    this.#positionLayer = L.layerGroup().addTo(this.#map);
    this.#resultLayer = L.layerGroup().addTo(this.#map);
  }

  async addBasemap(options) {
    await addBasemap(this.#map, { ...options, landStyle: () => this.#landStyle() });
  }

  showPosition(position) {
    this.#positionLayer.clearLayers();
    if (!position) return;
    L.circleMarker([position.lat, position.lon], {
      radius: 8, weight: 3, color: color("--ink"), fillColor: color("--surface"), fillOpacity: 1,
    })
      .bindTooltip(this.translator.t("map.you"))
      .addTo(this.#positionLayer);
  }

  showResult(result, selectedId) {
    this.#resultLayer.clearLayers();
    const routeIndex = new Map(result.options.map((o, i) => [o.id, i + 1]));
    for (const member of result.members) {
      L.polyline(member.path, {
        color: color(`--route-${routeIndex.get(member.option)}`), weight: 1.5, opacity: 0.35, interactive: false,
      }).addTo(this.#resultLayer);
    }
    const option = result.options.find((o) => o.id === selectedId);
    this.#drawZones(option);
    L.polyline(option.path, { color: color(`--route-${routeIndex.get(option.id)}`), weight: 5, opacity: 0.95 })
      .addTo(this.#resultLayer);
    this.showPosition(result.position);
    this.#map.fitBounds(L.latLngBounds(result.members.flatMap((m) => m.path)), { padding: [24, 24] });
  }

  invalidateSize() {
    this.#map.invalidateSize();
  }

  #drawZones(option) {
    for (const step of option.steps) {
      const level = confidenceLevel(step.confidence);
      const label = this.translator.t("map.zone", {
        h: step.hour, confidence: this.translator.t(`confidence.${level}`),
      });
      L.circle([step.lat, step.lon], {
        radius: step.zone_radius_nm * NM_IN_METERS, color: color(`--conf-${level}`), weight: 2,
        fillColor: color(`--conf-${level}`), fillOpacity: 0.15,
      })
        .bindTooltip(label)
        .addTo(this.#resultLayer);
    }
  }

  #landStyle() {
    return { color: color("--coast"), weight: 1, fillColor: color("--land"), fillOpacity: 1 };
  }
}

// Map colours follow the page theme tokens defined in styles/app.css.
function color(token) {
  return getComputedStyle(document.documentElement).getPropertyValue(token).trim();
}
