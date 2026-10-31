// The route options as selectable cards, each with a ring showing its chance of being the best.

import { createTermTip } from "./term-tip.js";
import { formatNumber } from "./display-format.js";
import { element } from "../dom.js";

const RING_RADIUS = 38;
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

    const head = element("span", "option-head");
    head.append(element("span", "option-name", t(`option.name.${option.id}`)));
    if (option.id === result.recommended_option) head.append(element("span", "badge", t("option.recommended")));

    const percent = Math.round(option.probability * 100);
    const eta = option.eta_delta_h === 0 ? t("option.eta_best")
      : t("option.eta_delta", { hours: formatNumber(option.eta_delta_h, this.translator.lang, Number.isInteger(option.eta_delta_h) ? 0 : 1) });
    const facts = element("span", "option-facts");
    facts.append(
      element("span", "option-kind", t(`option.kind.${option.kind}`)),
      element("span", "option-detail", t("option.members", { count: option.member_count, total: result.weather.member_count })),
      element("span", "option-detail", eta),
    );
    if (option.game_route) facts.append(element("span", "option-game", t("option.game_route")));

    const body = element("span", "option-body");
    body.append(this.#ring(percent), facts);
    button.append(head, body);
    item.append(button);
    return item;
  }

  #ring(percent) {
    const ring = element("span", "ring");
    ring.innerHTML = `<svg viewBox="0 0 100 100" aria-hidden="true">
      <circle class="ring-track" cx="50" cy="50" r="${RING_RADIUS}"/>
      <circle class="ring-value" cx="50" cy="50" r="${RING_RADIUS}"
        stroke-dasharray="${(RING_LENGTH * percent) / 100} ${RING_LENGTH}" transform="rotate(-90 50 50)"/></svg>`;
    const label = element("span", "ring-label");
    label.append(element("span", "ring-percent", `${percent} %`), element("span", "ring-caption", this.translator.t("option.ring_caption")));
    ring.append(label);
    return ring;
  }
}
