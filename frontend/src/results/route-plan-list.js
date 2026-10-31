// Route plan of the selected option as a list of orders: each leg keeps one heading and one sail until the
// next change (heading, sail, tack or gybe). Shows the next 48 h; tapping a leg shows its start on the map.

import { describeTwa, formatCoordinates, formatHeading, formatKnots, formatLocalTime, formatNumber } from "./display-format.js";
import { element } from "../dom.js";

const PLAN_HORIZON_H = 48;

export class RoutePlanList {
  constructor(container, translator, onSelectHour) {
    this.container = container;
    this.translator = translator;
    this.onSelectHour = onSelectHour;
  }

  render(result, option, selectedHour) {
    const t = (key, params) => this.translator.t(key, params);
    const head = element("div", "panel-head");
    head.append(element("h2", "panel-title", t("timeline.title", { option: t(`option.name.${option.id}`) })),
      element("span", "panel-subtitle", t("timeline.caption")));
    const legs = option.legs.filter((leg) => leg.start_hour < PLAN_HORIZON_H);
    const current = legs.findLast((leg) => leg.start_hour <= selectedHour);
    const list = element("ol", "plan-list");
    legs.forEach((leg) => list.append(this.#leg(result, leg, leg === current)));
    this.container.replaceChildren(head, list);
  }

  #leg(result, leg, selected) {
    const t = (key, params) => this.translator.t(key, params);
    const lang = this.translator.lang;
    const twa = describeTwa(leg.twa_deg);
    const button = element("button", "plan-step");
    button.type = "button";
    button.setAttribute("aria-pressed", String(selected));
    button.title = t("timeline.show_on_map");
    button.addEventListener("click", () => this.onSelectHour(Math.floor(leg.start_hour)));

    const when = element("span", "plan-when");
    when.append(
      element("span", "plan-hours", leg.start_hour === 0 ? t("wind.time_start") : t("wind.time_plus", { h: formatNumber(leg.start_hour, lang, 0) })),
      element("span", "plan-time", formatLocalTime(result.computed_at, leg.start_hour, lang)),
    );
    const main = element("span", "plan-main");
    main.append(
      element("span", "plan-order", `${formatHeading(leg.heading_deg)} · ${t(`sail.${leg.sail}`)}`),
      element("span", "plan-wind", this.#conditions(leg, twa)),
      element("span", "plan-position", formatCoordinates(leg)),
    );
    const duration = element("span", "plan-duration", this.#duration(leg.end_hour - leg.start_hour));
    button.append(when, main, duration);
    const item = element("li");
    item.append(button);
    return item;
  }

  // "Wind 10–12 kn · TWA 146° starboard · 7.9 kn", or "Wind 11 kn · …" when the wind does not change.
  #conditions(leg, twa) {
    const lang = this.translator.lang;
    const [min, max] = [formatNumber(leg.tws_min_kn, lang, 0), formatNumber(leg.tws_max_kn, lang, 0)];
    return this.translator.t(min === max ? "plan.wind_steady" : "plan.wind", {
      min, max, twa: `${twa.angle} ${this.translator.t(twa.tackKey)}`, speed: formatKnots(leg.speed_kn, this.translator),
    });
  }

  #duration(hours) {
    return hours >= 1
      ? this.translator.t("plan.leg_duration", { h: formatNumber(hours, this.translator.lang, Number.isInteger(hours) ? 0 : 1) })
      : this.translator.t("plan.leg_duration_min", { m: Math.round(hours * 60) });
  }
}
