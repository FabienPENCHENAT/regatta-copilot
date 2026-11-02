// The route options as a compact table, one selectable row per option: a small ring with the chance of being
// the best, the short name and its badges, then the outlook in aligned columns (+48 h, end): each track sailed
// in all 31 weathers, as miles gained (green ▲) or lost (red ▼) against the reference. The reference is the
// player's current route when it was recognised (a row of its own, first, with its distances to go), else the
// recommended option. Scenarios and worst case in a short tooltip.

import { formatLocalTime } from "./display-format.js";
import { colourSlot, inListOrder } from "./option-places.js";
import { createTermTip } from "./term-tip.js";
import { element } from "../dom.js";

const RING_RADIUS = 21;
const EVEN_NM = 10; // outlook gaps below this are within the cross-evaluation's error

const RING_LENGTH = 2 * Math.PI * RING_RADIUS;

export class OptionList {
  // onSelect(optionId): show an option; onFollow(optionId): the player says which previous option they follow.
  constructor(container, translator, { onSelect, onFollow }) {
    this.container = container;
    this.translator = translator;
    this.onSelect = onSelect;
    this.onFollow = onFollow;
  }

  // followed: the route the player has been following ({ optionId, computedAt, choices }), or null.
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
    const t = (key) => this.translator.t(key);
    const head = element("div", "option-head");
    head.title = t("option.table.legend");
    head.append(element("span"), element("span", "", t(againstCurrent ? "option.table.versus_current" : "option.table.versus_recommended")),
      ...hours.map((h) => element("span", "option-cell", this.#when(h))));
    return head;
  }

  // Not selectable: its orders are those of the previous computation, already on the player's screen. A menu
  // names the previous option it continues, to correct when the routes had not parted yet.
  #currentRow(result, followed) {
    const t = (key, params) => this.translator.t(key, params);
    const item = element("li");
    const row = element("div", "option-row current-route");
    row.title = t("option.current.tip");
    const origin = element("span", "option-facts current-route-origin");
    origin.append(this.#followPicker(followed));
    const text = element("span", "option-text");
    text.append(element("span", "option-name", t("option.current.name")), origin);
    row.append(element("span", "current-route-mark"), text, ...this.#distanceCells(result.current_route.outlook));
    item.append(row);
    return item;
  }

  #followPicker(followed) {
    const picker = element("select", "current-route-picker");
    const label = this.translator.t("option.current.pick", { time: formatLocalTime(followed.computedAt, 0, this.translator.lang) });
    picker.setAttribute("aria-label", label);
    picker.title = label;
    for (const choice of followed.choices) {
      const entry = element("option", "", this.translator.t("option.current.choice", {
        option: this.translator.t(`option.short.${choice.optionId}`), nm: this.#miles(choice.distanceNm),
      }));
      entry.value = choice.optionId;
      entry.selected = choice.optionId === followed.optionId;
      picker.append(entry);
    }
    // Sized to the longest label: the browser leaves the padding and the arrow out of a styled menu's width.
    picker.style.setProperty("--chars", String(Math.max(...[...picker.options].map((o) => o.text.length))));
    picker.addEventListener("change", () => this.onFollow(picker.value));
    return picker;
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
    name.append(element("span", "option-name", t(`option.short.${option.id}`)));
    if (option.id === result.recommended_option) name.append(element("span", "badge", t("option.recommended")));
    if (option.game_route) name.append(element("span", "badge badge-soft", t("option.game_badge")));
    if (option.kind === "shortest") name.append(element("span", "badge badge-soft", t("option.kind.shortest")));
    if (option.id === bestOnAverage(result)) name.append(element("span", "badge badge-best", t("option.best_average")));

    const isReference = !againstCurrent && option.id === result.recommended_option;
    const cells = !option.outlook?.length ? Array.from({ length: columns }, () => element("span", "option-cell"))
      : isReference ? this.#distanceCells(option.outlook) : this.#gainCells(option.outlook);
    row.title = [this.#summary(result, option), this.#outlookTip(result, option, isReference)].filter(Boolean).join("\n");
    row.append(this.#ring(option.probability === null ? null : Math.round(option.probability * 100)), name, ...cells);
    item.append(row);
    return item;
  }

  // The reference's own distances still to go, on its track in the 31 weathers.
  #distanceCells(outlook) {
    return outlook.map((row) => element("span", "option-cell distance", this.translator.t("unit.nm", { value: this.#miles(row.to_go_nm) })));
  }

  // Miles gained (▲, green) or lost (▼, red) against the reference; gaps under EVEN_NM are within the method's
  // error: "≈".
  #gainCells(outlook) {
    return outlook.map((row) => {
      if (Math.abs(row.gain_nm) < EVEN_NM) return element("span", "option-cell level", "≈");
      const gained = row.gain_nm > 0;
      return element("span", `option-cell ${gained ? "gain" : "loss"}`, `${gained ? "▲" : "▼"} ${this.#miles(row.gain_nm)}`);
    });
  }

  // "Best in 11 of 31 scenarios" (or the pending wording).
  #summary(result, option) {
    const t = (key, params) => this.translator.t(key, params);
    return option.probability === null ? t("option.ring_pending")
      : t("option.members", { count: option.member_count, total: result.weather.member_count });
  }

  #outlookTip(result, option, isReference) {
    if (!option.outlook?.length) return "";
    const t = (key, params) => this.translator.t(key, params);
    if (isReference) return t("option.outlook.tip_recommended");
    const total = result.weather.member_count;
    return option.outlook.map((row) => t("option.outlook.tip_row", {
      when: this.#when(row.hours), ahead: Math.round(row.ahead_share * total), total, worst: this.#miles(Math.min(row.worst_nm, 0)),
    })).join("\n");
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
