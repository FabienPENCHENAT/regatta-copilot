// Routes of a result: the 31 scenarios (thin), the selected option (thick), its target areas
// coloured by confidence, and the boat drawn where it should be at the selected hour.

import { confidenceLevel } from "../results/display-format.js";

const NM_IN_METERS = 1852;
const BOAT_SVG = `<svg viewBox="-12 -12 24 24" width="28" height="28" aria-hidden="true">
  <path d="M0 -10 C5 -4 5 4 3.5 9 L-3.5 9 C-5 4 -5 -4 0 -10 Z"/></svg>`;

export class RouteLayer {
  #routes;
  #boat;

  constructor(map, translator, colors) {
    this.translator = translator;
    this.color = colors;
    this.#routes = L.layerGroup().addTo(map);
    this.#boat = L.layerGroup().addTo(map);
  }

  render(result, option) {
    this.#routes.clearLayers();
    this.#idealRoute(result.ideal_route);
    const routeIndex = new Map(result.options.map((o, i) => [o.id, i + 1]));
    for (const member of result.members) {
      L.polyline(member.path, {
        color: this.color(`--route-${routeIndex.get(member.option)}`), weight: 1.4, opacity: 0.4, interactive: false,
      }).addTo(this.#routes);
    }
    option.steps.forEach((step) => this.#zone(step));
    L.polyline(option.path, { color: this.color(`--route-${routeIndex.get(option.id)}`), weight: 5, opacity: 0.95 })
      .addTo(this.#routes);
  }

  // The option path holds one point per hour from the start.
  showBoat(option, hour, heading) {
    this.#boat.clearLayers();
    const point = option.path[Math.min(hour, option.path.length - 1)];
    const icon = L.divIcon({
      className: "boat-icon",
      html: `<span style="transform: rotate(${heading}deg)">${BOAT_SVG}</span>`,
      iconSize: [28, 28],
    });
    L.marker(point, { icon, keyboard: false })
      .bindTooltip(hour === 0 ? this.translator.t("map.you") : this.translator.t("map.boat_at", { h: hour }))
      .addTo(this.#boat);
  }

  // Whole track to the finish, for the eye only: a soft halo under a dashed line.
  #idealRoute(ideal) {
    if (!ideal) return;
    const label = this.translator.t("map.ideal_route", { distance: Math.round(ideal.distance_nm).toLocaleString(this.translator.lang) });
    L.polyline(ideal.path, { color: this.color("--ideal-halo"), weight: 8, opacity: 0.55, interactive: false })
      .addTo(this.#routes);
    L.polyline(ideal.path, { color: this.color("--ideal-line"), weight: 2, dashArray: "8 6" })
      .bindTooltip(label, { sticky: true })
      .addTo(this.#routes);
  }

  // Target area: a faint circle of the zone size plus a glowing dot coloured by confidence.
  #zone(step) {
    const level = confidenceLevel(step.confidence);
    const label = this.translator.t("map.zone", { h: step.hour, confidence: this.translator.t(`confidence.${level}`) });
    L.circle([step.lat, step.lon], {
      radius: step.zone_radius_nm * NM_IN_METERS, color: this.color(`--zone-${level}`), weight: 1, opacity: 0.7,
      fillColor: this.color(`--zone-${level}`), fillOpacity: 0.1, interactive: false,
    }).addTo(this.#routes);
    const glow = L.divIcon({ className: `zone-glow ${level}`, html: "<span></span>", iconSize: [44, 44] });
    L.marker([step.lat, step.lon], { icon: glow, keyboard: false }).bindTooltip(label).addTo(this.#routes);
  }
}
