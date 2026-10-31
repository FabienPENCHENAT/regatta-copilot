// The route options as compact selectable cards: a small ring with the chance of being the best,
// the option name, and one short line (type, arrival gap). Full details in the tooltip.

import { createTermTip } from "./term-tip.js";
import { formatNumber } from "./display-format.js";
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

    const facts = element("span", "option-facts", `${t(`option.kind_short.${option.kind}`)} · ${this.#eta(option)}`);
    button.title = option.probability === null
      ? `${t(`option.kind.${option.kind}`)} — ${t("option.ring_pending")}`
      : `${t(`option.kind.${option.kind}`)} — ${t("option.members", { count: option.member_count, total: result.weather.member_count })}`;

    const text = element("span", "option-text");
    text.append(name, facts);
    button.append(this.#ring(option.probability === null ? null : Math.round(option.probability * 100)), text);
    item.append(button);
    return item;
  }

  #eta(option) {
    if (option.eta_delta_h === 0) return this.translator.t("option.eta_short_best");
    const hours = formatNumber(option.eta_delta_h, this.translator.lang, Number.isInteger(option.eta_delta_h) ? 0 : 1);
    return this.translator.t("option.eta_short", { hours });
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
