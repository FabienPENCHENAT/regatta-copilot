// The route options as compact selectable cards: a small ring with the chance of being the best,
// the option name, one short line (type, number of scenarios) and the outlook: each option's track sailed in all
// 31 weathers, as distance still to go for the reference or miles gained or lost against it for the others, at
// +48 h and at the end. The reference is the player's current route when it was recognised (a card of its own,
// first), else the recommended option. Full details in the tooltip.

import { formatLocalTime } from "./display-format.js";
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

  // followed: the route the player has been following ({ optionId, computedAt }), or null.
  render(result, selectedId, followed) {
    const title = element("h2", "dock-title");
    title.append(this.translator.t("options.title"), createTermTip(this.translator, "tip.probability"));
    const list = element("ul", "option-list");
    if (result.current_route && followed) list.append(this.#currentCard(result, followed));
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

  // Not selectable: its orders are those of the previous computation, already on the player's screen.
  #currentCard(result, followed) {
    const t = (key, params) => this.translator.t(key, params);
    const item = element("li");
    const card = element("div", "glass option-card current-route");
    card.title = t("option.current.tip");
    const name = element("span", "option-name-row");
    name.append(element("span", "option-name", t("option.current.name")));
    const text = element("span", "option-text");
    text.append(
      name,
      element("span", "option-facts", t("option.current.origin", {
        option: t(`option.name.${followed.optionId}`), time: formatLocalTime(followed.computedAt, 0, this.translator.lang),
      })),
      this.#referenceLine(result.current_route.outlook),
    );
    card.append(element("span", "current-route-mark"), text);
    item.append(card);
    return item;
  }

  // How many scenarios back the option: the grouping the advice relies on. (The arrival gap is not shown:
  // each option is measured in its own weather, so the figure would not be comparable.)
  #support(result, option) {
    if (option.probability === null) return this.translator.t("option.game_forecast_only");
    return this.translator.t("option.members_short", { count: option.member_count, total: result.weather.member_count });
  }

  // In words: the reference gives the distance still to go, the others how far ahead or behind it they are;
  // gaps under EVEN_NM are within the method's error and read "level".
  #outlook(result, option) {
    if (!option.outlook?.length) return null;
    const t = (key, params) => this.translator.t(key, params);
    const againstCurrent = result.outlook_reference === "current_route";
    if (!againstCurrent && option.id === result.recommended_option) {
      return { line: this.#referenceLine(option.outlook), tip: t("option.outlook.tip_recommended") };
    }
    const line = element("span", "option-outlook");
    line.append(t(againstCurrent ? "option.outlook.versus_current" : "option.outlook.versus"));
    option.outlook.forEach((row, i) => {
      line.append(i ? ", " : " ");
      const state = row.gain_nm >= EVEN_NM ? "ahead" : row.gain_nm <= -EVEN_NM ? "behind" : "level";
      line.append(element("span", state === "ahead" ? "gain" : state === "behind" ? "loss" : "",
        t(`option.outlook.${state}`, { nm: this.#miles(row.gain_nm), when: this.#when(row.hours) })));
    });
    const total = result.weather.member_count;
    const tip = [t(againstCurrent ? "option.outlook.tip_other_current" : "option.outlook.tip_other"),
      ...option.outlook.map((row) => t("option.outlook.tip_row", {
        when: this.#when(row.hours), ahead: Math.round(row.ahead_share * total), total, worst: this.#miles(row.worst_nm),
      }))].join("\n");
    return { line, tip };
  }

  // Distance still to go at +48 h and at the end, on the reference's track in the 31 weathers.
  #referenceLine(outlook) {
    const [first, last] = [outlook[0], outlook.at(-1)];
    return element("span", "option-outlook", this.translator.t("option.outlook.reference", {
      nm: this.#miles(first.to_go_nm), when: this.#when(first.hours),
      nm_end: this.#miles(last.to_go_nm), when_end: this.#when(last.hours),
    }));
  }

  #when(hours) {
    return hours >= 72 ? this.translator.t("option.outlook.days", { d: Math.round(hours / 24) }) : `+${hours} h`;
  }

  #miles(value) {
    return Math.round(Math.abs(value)).toLocaleString(this.translator.lang);
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
// weathers), the furthest ahead if several; null when the recommended option is best or level. Gains may be
// measured against the current route: the recommended option's own gain is then taken off.
function bestOnAverage(result) {
  const gain = (option) => option.outlook?.at(-1)?.gain_nm ?? 0;
  const recommended = result.options.find((o) => o.id === result.recommended_option);
  const base = recommended ? gain(recommended) : 0;
  const best = result.options.filter((o) => o.id !== result.recommended_option && gain(o) - base >= EVEN_NM)
    .sort((a, b) => gain(b) - gain(a))[0];
  return best?.id ?? null;
}
