// The route options as compact selectable cards: a small ring with the chance of being the best,
// the option name, one short line (type, number of scenarios) and the outlook: each option's track sailed in all
// 31 weathers, as distance still to go (recommended option) or miles gained or lost against it (others), at
// +48 h and at the end. Full details in the tooltip.

import { colourSlot, inListOrder } from "./option-places.js";
import { createTermTip } from "./term-tip.js";
import { element } from "../dom.js";

const RING_RADIUS = 21;
const EVEN_NM = 10; // outlook gaps below this are within the cross-evaluation's error

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
    // Listed as on the chart, not by probability: an option keeps its place when the percentages move.
    for (const option of inListOrder(result.options)) list.append(this.#card(result, option, option.id === selectedId));
    this.container.replaceChildren(title, list);
  }

  #card(result, option, selected) {
    const t = (key, params) => this.translator.t(key, params);
    const item = element("li");
    const button = element("button", "glass option-card");
    button.type = "button";
    button.dataset.route = String(colourSlot(option.id));
    button.setAttribute("aria-pressed", String(selected));
    button.addEventListener("click", () => this.onSelect(option.id));

    const name = element("span", "option-name-row");
    name.append(element("span", "option-name", t(`option.name.${option.id}`)));
    if (option.id === result.recommended_option) name.append(element("span", "badge", t("option.recommended")));
    if (option.game_route) name.append(element("span", "badge badge-soft", t("option.game_badge")));
    if (option.id === bestOnAverage(result)) name.append(element("span", "badge badge-best", t("option.best_average")));

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

  // In words: the recommended option gives the reference (distance still to go), the others how far ahead or
  // behind it they are; gaps under EVEN_NM are within the method's error and read "level".
  #outlook(result, option) {
    if (!option.outlook?.length) return null;
    const t = (key, params) => this.translator.t(key, params);
    const lang = this.translator.lang;
    const when = (hours) => (hours >= 72 ? t("option.outlook.days", { d: Math.round(hours / 24) }) : `+${hours} h`);
    const miles = (value) => Math.round(Math.abs(value)).toLocaleString(lang);
    const line = element("span", "option-outlook");
    if (option.id === result.recommended_option) {
      const [first, last] = [option.outlook[0], option.outlook.at(-1)];
      line.append(t("option.outlook.reference", {
        nm: miles(first.to_go_nm), when: when(first.hours), nm_end: miles(last.to_go_nm), when_end: when(last.hours),
      }));
      return { line, tip: t("option.outlook.tip_recommended") };
    }
    line.append(t("option.outlook.versus"));
    option.outlook.forEach((row, i) => {
      line.append(i ? ", " : " ");
      const state = row.gain_nm >= EVEN_NM ? "ahead" : row.gain_nm <= -EVEN_NM ? "behind" : "level";
      line.append(element("span", state === "ahead" ? "gain" : state === "behind" ? "loss" : "",
        t(`option.outlook.${state}`, { nm: miles(row.gain_nm), when: when(row.hours) })));
    });
    const total = result.weather.member_count;
    const tip = [t("option.outlook.tip_other"), ...option.outlook.map((row) => t("option.outlook.tip_row", {
      when: when(row.hours), ahead: Math.round(row.ahead_share * total), total, worst: miles(row.worst_nm),
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

// The option ahead of the recommended one by at least EVEN_NM on average at the last hour measured (the 31
// weathers), the furthest ahead if several; null when the recommended option is best or level.
function bestOnAverage(result) {
  const gain = (option) => option.outlook?.at(-1)?.gain_nm ?? 0;
  const best = result.options.filter((o) => o.id !== result.recommended_option && gain(o) >= EVEN_NM)
    .sort((a, b) => gain(b) - gain(a))[0];
  return best?.id ?? null;
}
