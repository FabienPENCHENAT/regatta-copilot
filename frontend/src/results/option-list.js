// The route options as compact selectable cards: a small ring with the chance of being the best,
// the option name, one short line (type, number of scenarios) and the outlook: each option's track sailed in all
// 31 weathers, as distance still to go (recommended option) or miles gained or lost against it (others), at
// +48 h and at the end. Full details in the tooltip.

import { createTermTip } from "./term-tip.js";
import { element } from "../dom.js";

const RING_RADIUS = 21;
const RING_LENGTH = 2 * Math.PI * RING_RADIUS;

export class OptionList {
  constructor(container, translator, onSelect) {
    this.container = container;
    this.translator = translator;
    this.onSelect = onSelect;
  }

  render(result, selectedId) {
    const title = element("h2", "dock-title");
    title.append(this.translator.t("options.title"), createTermTip(this.translator, "tip.probability"));
    const list = element("ul", "option-list");
    result.options.forEach((option, index) => list.append(this.#card(result, option, index, option.id === selectedId)));
    this.container.replaceChildren(title, list);
  }

  #card(result, option, index, selected) {
    const t = (key, params) => this.translator.t(key, params);
    const item = element("li");
    const button = element("button", "glass option-card");
    button.type = "button";
    button.dataset.route = String(index + 1);
    button.setAttribute("aria-pressed", String(selected));
    button.addEventListener("click", () => this.onSelect(option.id));

    const name = element("span", "option-name-row");
    name.append(element("span", "option-name", t(`option.name.${option.id}`)));
    if (option.id === result.recommended_option) name.append(element("span", "badge", t("option.recommended")));
    if (option.game_route) name.append(element("span", "badge badge-soft", t("option.game_badge")));

    const facts = element("span", "option-facts", `${t(`option.kind_short.${option.kind}`)} · ${this.#support(result, option)}`);
    button.title = option.probability === null
      ? `${t(`option.kind.${option.kind}`)} — ${t("option.ring_pending")}`
      : `${t(`option.kind.${option.kind}`)} — ${t("option.members", { count: option.member_count, total: result.weather.member_count })}`;

    const text = element("span", "option-text");
    text.append(name, facts);
    const outlook = this.#outlook(result, option);
    if (outlook) {
      text.append(outlook.line);
      button.title += `\n${outlook.tip}`;
    }
    button.append(this.#ring(option.probability === null ? null : Math.round(option.probability * 100)), text);
    item.append(button);
    return item;
  }

  // How many scenarios back the option: the grouping the advice relies on. (The arrival gap is not shown:
  // each option is measured in its own weather, so the figure would not be comparable.)
  #support(result, option) {
    if (option.probability === null) return this.translator.t("option.game_forecast_only");
    return this.translator.t("option.members_short", { count: option.member_count, total: result.weather.member_count });
  }

  #outlook(result, option) {
    if (!option.outlook?.length) return null;
    const t = (key, params) => this.translator.t(key, params);
    const lang = this.translator.lang;
    const recommended = option.id === result.recommended_option;
    const when = (hours) => (hours >= 72 ? t("option.outlook.days", { d: Math.round(hours / 24) }) : `+${hours} h`);
    const miles = (value, sign) => value.toLocaleString(lang, { maximumFractionDigits: 0, signDisplay: sign });
    const line = element("span", "option-outlook");
    option.outlook.forEach((row, i) => {
      if (i) line.append(" · ");
      if (recommended) {
        line.append(t("option.outlook.to_go", { when: when(row.hours), nm: miles(row.to_go_nm, "auto") }));
        return;
      }
      const gain = element("span", row.gain_nm >= 0.5 ? "gain" : row.gain_nm <= -0.5 ? "loss" : "",
        t("option.outlook.gain", { when: when(row.hours), nm: miles(row.gain_nm, "exceptZero") }));
      line.append(gain);
    });
    const total = result.weather.member_count;
    const tip = recommended ? t("option.outlook.tip_recommended") : [t("option.outlook.tip_other"),
      ...option.outlook.map((row) => t("option.outlook.tip_row", {
        when: when(row.hours), ahead: Math.round(row.ahead_share * total), total, worst: miles(row.worst_nm, "exceptZero"),
      }))].join("\n");
    return { line, tip };
  }

  // percent null: no probability yet (single forecast): an empty ring with a dash.
  #ring(percent) {
    const ring = element("span", percent === null ? "ring pending" : "ring");
    ring.innerHTML = `<svg viewBox="0 0 50 50" aria-hidden="true">
      <circle class="ring-track" cx="25" cy="25" r="${RING_RADIUS}"/>
      <circle class="ring-value" cx="25" cy="25" r="${RING_RADIUS}"
        stroke-dasharray="${(RING_LENGTH * (percent ?? 0)) / 100} ${RING_LENGTH}" transform="rotate(-90 25 25)"/></svg>`;
    ring.append(element("span", "ring-percent", percent === null ? "—" : `${percent}%`));
    ring.setAttribute("aria-label", percent === null
      ? this.translator.t("option.ring_pending") : this.translator.t("option.probability", { percent }));
    return ring;
  }
}
