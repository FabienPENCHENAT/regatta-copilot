// The route options as a compact table, one selectable row per option: a small ring with the chance of being
// the best, the name and its badges, then the outlook in aligned columns (+48 h, end): each track sailed in all
// 31 weathers, as miles gained or lost against the reference. The reference is the player's current route when
// it was recognised (a row of its own, first, with its distances to go), else the recommended option. Details
// (kind, scenarios, worst case) in the row's tooltip.

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
    const t = (key, params) => this.translator.t(key, params);
    const title = element("h2", "dock-title");
    title.append(t("options.title"), createTermTip(this.translator, "tip.probability"));
    const againstCurrent = Boolean(result.current_route && followed);
    const hours = (result.options.find((o) => o.outlook?.length)?.outlook ?? []).map((row) => row.hours);
    const table = element("div", "glass option-table");
    table.style.setProperty("--outlook-columns", String(hours.length));
    if (hours.length) table.append(this.#head(hours, againstCurrent));
    const list = element("ul", "option-list");
    if (againstCurrent) list.append(this.#currentRow(result, followed));
    for (const option of inListOrder(result.options)) {
      list.append(this.#row(result, option, option.id === selectedId, againstCurrent, hours.length));
    }
    table.append(list);
    this.container.replaceChildren(title, table);
  }

  #head(hours, againstCurrent) {
    const head = element("div", "option-head");
    head.title = this.translator.t(againstCurrent ? "option.table.versus_current" : "option.table.versus_recommended");
    head.append(element("span"), element("span"), ...hours.map((h) => element("span", "option-cell", this.#when(h))));
    return head;
  }

  // Not selectable: its orders are those of the previous computation, already on the player's screen.
  #currentRow(result, followed) {
    const t = (key, params) => this.translator.t(key, params);
    const item = element("li");
    const row = element("div", "option-row current-route");
    row.title = t("option.current.tip");
    const text = element("span", "option-text");
    text.append(
      element("span", "option-name", t("option.current.name")),
      element("span", "option-facts", t("option.current.origin", {
        option: t(`option.name.${followed.optionId}`), time: formatLocalTime(followed.computedAt, 0, this.translator.lang),
      })),
    );
    row.append(element("span", "current-route-mark"), text, ...this.#distanceCells(result.current_route.outlook));
    item.append(row);
    return item;
  }

  #row(result, option, selected, againstCurrent, columns) {
    const t = (key, params) => this.translator.t(key, params);
    const item = element("li");
    const row = element("button", "option-row");
    row.type = "button";
    row.dataset.route = String(colourSlot(option.id));
    row.setAttribute("aria-pressed", String(selected));
    row.addEventListener("click", () => this.onSelect(option.id));

    const name = element("span", "option-name-row");
    name.append(element("span", "option-name", t(`option.name.${option.id}`)));
    if (option.id === result.recommended_option) name.append(element("span", "badge", t("option.recommended")));
    if (option.game_route) name.append(element("span", "badge badge-soft", t("option.game_badge")));
    if (option.kind === "shortest") name.append(element("span", "badge badge-soft", t("option.kind.shortest")));
    if (option.id === bestOnAverage(result)) name.append(element("span", "badge badge-best", t("option.best_average")));

    const isReference = !againstCurrent && option.id === result.recommended_option;
    const cells = !option.outlook?.length ? Array.from({ length: columns }, () => element("span", "option-cell"))
      : isReference ? this.#distanceCells(option.outlook) : this.#gainCells(option.outlook);
    row.title = [this.#summary(result, option), this.#outlookTip(result, option, isReference, againstCurrent)]
      .filter(Boolean).join("\n");
    row.append(this.#ring(option.probability === null ? null : Math.round(option.probability * 100)), name, ...cells);
    item.append(row);
    return item;
  }

  // The reference's own distances still to go, on its track in the 31 weathers.
  #distanceCells(outlook) {
    return outlook.map((row) => element("span", "option-cell distance", this.translator.t("unit.nm", { value: this.#miles(row.to_go_nm) })));
  }

  // Miles ahead (+) or behind (−) the reference; gaps under EVEN_NM are within the method's error: "=".
  #gainCells(outlook) {
    return outlook.map((row) => {
      if (Math.abs(row.gain_nm) < EVEN_NM) return element("span", "option-cell level", "=");
      const sign = row.gain_nm > 0 ? "+" : "−";
      return element("span", `option-cell ${row.gain_nm > 0 ? "gain" : "loss"}`, `${sign}${this.#miles(row.gain_nm)}`);
    });
  }

  // "Weather positioning — 11 of 31 scenarios" (or the pending / single-forecast wording).
  #summary(result, option) {
    const t = (key, params) => this.translator.t(key, params);
    return option.probability === null
      ? `${t(`option.kind.${option.kind}`)} — ${t("option.ring_pending")}`
      : `${t(`option.kind.${option.kind}`)} — ${t("option.members", { count: option.member_count, total: result.weather.member_count })}`;
  }

  #outlookTip(result, option, isReference, againstCurrent) {
    if (!option.outlook?.length) return "";
    const t = (key, params) => this.translator.t(key, params);
    if (isReference) return t("option.outlook.tip_recommended");
    const total = result.weather.member_count;
    return [t(againstCurrent ? "option.outlook.tip_other_current" : "option.outlook.tip_other"),
      ...option.outlook.map((row) => t("option.outlook.tip_row", {
        when: this.#when(row.hours), ahead: Math.round(row.ahead_share * total), total, worst: this.#miles(row.worst_nm),
      }))].join("\n");
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
