// Routes of a result: the computed track, the scenario routes (thin), the selected option (thick) with a
// numbered point at each change of orders (same numbers as the route plan), and the boat at the selected hour.

import { formatHeading } from "../results/display-format.js";
import { legAt, planLegs } from "../results/plan-legs.js";

const BOAT_SVG = `<svg viewBox="-12 -12 24 24" width="28" height="28" aria-hidden="true">
  <path d="M0 -10 C5 -4 5 4 3.5 9 L-3.5 9 C-5 4 -5 -4 0 -10 Z"/></svg>`;

export class RouteLayer {
  #routes;
  #boat;

  constructor(map, translator, colors, onSelectHour) {
    this.translator = translator;
    this.color = colors;
    this.onSelectHour = onSelectHour;
    this.#routes = L.layerGroup().addTo(map);
    this.#boat = L.layerGroup().addTo(map);
  }

  render(result, option, hour) {
    this.#routes.clearLayers();
    this.#idealRoute(result.ideal_route);
    const routeIndex = new Map(result.options.map((o, i) => [o.id, i + 1]));
    for (const member of result.members) {
      L.polyline(member.path, {
        color: this.color(`--route-${routeIndex.get(member.option)}`), weight: 1.4, opacity: 0.4, interactive: false,
      }).addTo(this.#routes);
    }
    L.polyline(option.path, { color: this.color(`--route-${routeIndex.get(option.id)}`), weight: 5, opacity: 0.95 })
      .addTo(this.#routes);
    this.#legMarkers(option, hour);
  }

  #legMarkers(option, hour) {
    const legs = planLegs(option);
    const current = legAt(legs, hour);
    legs.forEach((leg, index) => {
      const icon = L.divIcon({
        className: `leg-marker${leg === current ? " current" : ""}`, html: `<span>${index + 1}</span>`, iconSize: [24, 24],
      });
      const label = `${index + 1} · ${formatHeading(leg.heading_deg)} · ${this.translator.t(`sail.${leg.sail}`)}`;
      L.marker([leg.lat, leg.lon], { icon, keyboard: false, zIndexOffset: leg === current ? 500 : 0 })
        .bindTooltip(label)
        .on("click", () => this.onSelectHour(Math.floor(leg.start_hour)))
        .addTo(this.#routes);
    });
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

  // Whole computed track, for the eye only: a soft halo under a dashed line.
  #idealRoute(ideal) {
    if (!ideal) return;
    const label = this.translator.t("map.ideal_route", {
      distance: Math.round(ideal.distance_nm).toLocaleString(this.translator.lang),
      to_go: Math.round(ideal.to_go_nm ?? 0).toLocaleString(this.translator.lang),
    });
    L.polyline(ideal.path, { color: this.color("--ideal-halo"), weight: 8, opacity: 0.55, interactive: false })
      .addTo(this.#routes);
    L.polyline(ideal.path, { color: this.color("--ideal-line"), weight: 2, dashArray: "8 6" })
      .bindTooltip(label, { sticky: true })
      .addTo(this.#routes);
  }

}
