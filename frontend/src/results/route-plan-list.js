// Route plan of the selected option as a list of orders: each leg keeps one heading and one sail until the
// next change (heading, sail, tack or gybe). Numbered like the points on the map; tapping a leg shows it there.

import { describeTwa, formatCoordinates, formatHeading, formatHoursMinutes, formatKnots, formatLocalTime, formatNumber } from "./display-format.js";
import { legAt, planLegs } from "./plan-legs.js";
import { element } from "../dom.js";

export class RoutePlanList {
  #shownLeg = null;

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
    const legs = planLegs(option);
    const current = legAt(legs, selectedHour);
    const list = element("ol", "plan-list");
    legs.forEach((leg, index) => list.append(this.#leg(result, leg, index + 1, leg === current)));
    this.container.replaceChildren(head, list);
    this.#reveal(list, legs.indexOf(current), `${option.id}:${current?.start_hour}`);
  }

  // When the order being sailed changes (a point clicked on the map, the time bar, another option), its line is
  // scrolled into view; a plain redraw leaves the player's own scrolling alone.
  #reveal(list, index, key) {
    if (index < 0 || key === this.#shownLeg) return;
    this.#shownLeg = key;
    list.children[index]?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  #leg(result, leg, number, selected) {
    const t = (key, params) => this.translator.t(key, params);
    const lang = this.translator.lang;
    const twa = describeTwa(leg.twa_deg);
    const button = element("button", "plan-step");
    button.type = "button";
    button.setAttribute("aria-pressed", String(selected));
    button.title = t("timeline.show_on_map");
    button.addEventListener("click", () => this.onSelectHour(leg.start_hour));

    const when = element("span", "plan-when");
    when.append(
      element("span", "plan-number", String(number)),
      element("span", "plan-hours", leg.start_hour === 0 ? t("wind.time_start") : `+${formatHoursMinutes(leg.start_hour)}`),
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
    return formatHoursMinutes(hours);
  }
}
