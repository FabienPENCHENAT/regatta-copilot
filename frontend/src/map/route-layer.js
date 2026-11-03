// Routes of a result: the computed track, the scenario routes (thin), the player's current route (dashed), the
// selected option (thick) with a numbered point at each change of orders (same numbers as the route plan), and
// the boat at the selected hour, whose label gives what it sails there.

import {
  describeTwa, formatHeading, formatHoursMinutes, formatKnots, formatLocalTime, formatNumber,
} from "../results/display-format.js";
import { colourSlot } from "../results/option-places.js";
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

  render(result, option, hour, followed) {
    this.#routes.clearLayers();
    this.#idealRoute(result.ideal_route);
    if (followed) this.#currentRoute(followed);
    for (const member of result.members) {
      L.polyline(member.line ?? member.path, {
        color: this.color(`--route-${colourSlot(member.option)}`), weight: 1.4, opacity: 0.4, interactive: false,
      }).addTo(this.#routes);
    }
    // Every route point (quarter-hours at first), so the leg markers sit on the line; older results: hourly.
    L.polyline(option.line ?? option.path, { color: this.color(`--route-${colourSlot(option.id)}`), weight: 5, opacity: 0.95 })
      .addTo(this.#routes);
    this.#legMarkers(option, hour);
  }

  #legMarkers(option, hour) {
    const legs = planLegs(option);
    const current = legAt(legs, hour);
    legs.forEach((leg, index) => {
      const icon = L.divIcon({
        className: `leg-marker${leg === current ? " current" : ""}`, html: `<span>${index + 1}</span>`, iconSize: [12, 12],
      });
      // The number is already on the point: the label gives the order and the speed to expect. Clicking it puts
      // the boat there (the boat's own label then gives the details); the order being sailed pulses.
      const label = `${formatHeading(leg.heading_deg)} · ${this.translator.t(`sail.${leg.sail}`)} · ${formatKnots(leg.speed_kn, this.translator)}`;
      L.marker([leg.lat, leg.lon], { icon, keyboard: false, zIndexOffset: leg === current ? 500 : 0 })
        .bindTooltip(label, { direction: "top", offset: [0, -6], className: "leg-label" })
        .on("click", () => this.onSelectHour(leg.start_hour))
        .addTo(this.#routes);
    });
  }

  // The boat on its numbered point at the start of an order, else between the hourly path points. Its label stays
  // open at every hour (beyond the 48 h plan too): option, time, then heading, sail, speed and wind right there.
  showBoat(option, hour, heading, startIso) {
    this.#boat.clearLayers();
    const leg = option.legs.find((l) => l.start_hour === hour);
    const point = leg ? [leg.lat, leg.lon] : pathPointAt(option.path, hour);
    const icon = L.divIcon({
      className: "boat-icon",
      html: `<span style="transform: rotate(${heading}deg)">${BOAT_SVG}</span>`,
      iconSize: [28, 28],
    });
    const title = hour === 0 ? this.translator.t("map.you") : this.#boatTitle(option, hour, startIso);
    L.marker(point, { icon, keyboard: false, zIndexOffset: 1000 })
      .bindTooltip(`<span class="boat-label-title">${title}</span><br>${this.#boatSettings(option, hour)}`,
        { permanent: true, direction: "bottom", offset: [0, 14], className: "boat-label" })
      .addTo(this.#boat);
  }

  #boatTitle(option, hour, startIso) {
    const t = (key, params) => this.translator.t(key, params);
    const legs = planLegs(option);
    const current = legAt(legs, hour);
    const params = {
      option: t(`option.name.${option.id}`), h: formatHoursMinutes(hour),
      time: formatLocalTime(startIso, hour, this.translator.lang), n: legs.indexOf(current) + 1,
    };
    return current && hour < (legs.at(-1)?.end_hour ?? 0) ? t("map.boat_at", params) : t("map.boat_at_plain", params);
  }

  // "234° · Spi léger · 13,3 nd · Vent 12 nd · TWA 140° bâbord".
  #boatSettings(option, hour) {
    const t = (key, params) => this.translator.t(key, params);
    const now = settingsAt(option, hour);
    const twa = describeTwa(now.twa_deg);
    const wind = t("plan.wind_steady", {
      min: formatNumber(now.tws_kn, this.translator.lang, 0), twa: `${twa.angle} ${t(twa.tackKey)}`,
    });
    return `${formatHeading(now.heading_deg)} · ${t(`sail.${now.sail}`)} · ${formatKnots(now.speed_kn, this.translator)} · ${wind}`;
  }

  // The rest of the route the player has been following, from the boat: dashed, in the ink colour, under the options.
  #currentRoute(followed) {
    const label = this.translator.t("map.current_route", {
      option: this.translator.t(`option.name.${followed.optionId}`),
      time: formatLocalTime(followed.computedAt, 0, this.translator.lang),
    });
    const { position } = followed.request;
    L.polyline([[position.lat, position.lon], ...followed.path],
      { color: this.color("--ink"), weight: 3.5, opacity: 0.9, dashArray: "1 8", lineCap: "round" })
      .bindTooltip(label, { sticky: true })
      .addTo(this.#routes);
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

// What the boat sails at `hour`: the hourly settings, or the order's own when it started since the last whole
// hour (a numbered point clicked) or on results saved before `hourly` existed (wind: middle of the order's range).
function settingsAt(option, hour) {
  const leg = legAt(option.legs, hour) ?? option.legs[0];
  const hourly = option.hourly?.[Math.min(Math.floor(hour), option.hourly.length - 1)];
  if (hourly && !(leg && leg.start_hour > Math.floor(hour))) return hourly;
  if (!leg) return option.now;
  return { ...leg, tws_kn: (leg.tws_min_kn + leg.tws_max_kn) / 2 };
}

// Position at a (possibly fractional) hour on a path holding one point per hour.
function pathPointAt(path, hour) {
  const last = path.length - 1;
  const before = Math.min(Math.floor(hour), last);
  const after = Math.min(before + 1, last);
  const share = Math.min(Math.max(hour - before, 0), 1);
  return [0, 1].map((k) => path[before][k] + (path[after][k] - path[before][k]) * share);
}
