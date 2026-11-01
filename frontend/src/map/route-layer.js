// Routes of a result: the computed track, the scenario routes (thin), the selected option (thick) with a
// numbered point at each change of orders (same numbers as the route plan), and the boat at the selected hour.

import { formatHeading, formatHoursMinutes, formatLocalTime } from "../results/display-format.js";
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
      L.polyline(member.line ?? member.path, {
        color: this.color(`--route-${routeIndex.get(member.option)}`), weight: 1.4, opacity: 0.4, interactive: false,
      }).addTo(this.#routes);
    }
    // Every route point (quarter-hours at first), so the leg markers sit on the line; older results: hourly.
    L.polyline(option.line ?? option.path, { color: this.color(`--route-${routeIndex.get(option.id)}`), weight: 5, opacity: 0.95 })
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
      // The order being sailed at the shown hour pulses and keeps its label open.
      L.marker([leg.lat, leg.lon], { icon, keyboard: false, zIndexOffset: leg === current ? 500 : 0 })
        .bindTooltip(label, leg === current
          ? { permanent: true, direction: "top", offset: [0, -14], className: "leg-label current" }
          : { direction: "top", offset: [0, -12], className: "leg-label" })
        .on("click", () => this.onSelectHour(leg.start_hour))
        .addTo(this.#routes);
    });
  }

  // At the start of an order the boat sits on its numbered point (whose label says it all); otherwise it sits
  // between the hourly path points and keeps its own label open: option, time, order being sailed.
  showBoat(option, hour, heading, startIso) {
    this.#boat.clearLayers();
    const leg = option.legs.find((l) => l.start_hour === hour);
    const point = leg ? [leg.lat, leg.lon] : pathPointAt(option.path, hour);
    const icon = L.divIcon({
      className: "boat-icon",
      html: `<span style="transform: rotate(${heading}deg)">${BOAT_SVG}</span>`,
      iconSize: [28, 28],
    });
    const between = hour > 0 && !leg;
    L.marker(point, { icon, keyboard: false })
      .bindTooltip(hour === 0 ? this.translator.t("map.you") : this.#boatLabel(option, hour, startIso), between
        ? { permanent: true, direction: "bottom", offset: [0, 14], className: "boat-label" } : {})
      .addTo(this.#boat);
  }

  #boatLabel(option, hour, startIso) {
    const t = (key, params) => this.translator.t(key, params);
    const legs = planLegs(option);
    const current = legAt(legs, hour);
    const params = {
      option: t(`option.name.${option.id}`), h: formatHoursMinutes(hour),
      time: formatLocalTime(startIso, hour, this.translator.lang), n: legs.indexOf(current) + 1,
    };
    return current && hour < (legs.at(-1)?.end_hour ?? 0) ? t("map.boat_at", params) : t("map.boat_at_plain", params);
  }

  // Whole computed track on the game's weather, for the eye only: a thin, faint dashed line under the options.
  #idealRoute(ideal) {
    if (!ideal) return;
    const label = this.translator.t("map.ideal_route", {
      distance: Math.round(ideal.distance_nm).toLocaleString(this.translator.lang),
      to_go: Math.round(ideal.to_go_nm ?? 0).toLocaleString(this.translator.lang),
    });
    L.polyline(ideal.path, { color: this.color("--ideal-halo"), weight: 1.5, opacity: 0.35, dashArray: "4 6" })
      .bindTooltip(label, { sticky: true })
      .addTo(this.#routes);
  }

}

// Position at a (possibly fractional) hour on a path holding one point per hour.
function pathPointAt(path, hour) {
  const last = path.length - 1;
  const before = Math.min(Math.floor(hour), last);
  const after = Math.min(before + 1, last);
  const share = Math.min(Math.max(hour - before, 0), 1);
  return [0, 1].map((k) => path[before][k] + (path[after][k] - path[before][k]) * share);
}
