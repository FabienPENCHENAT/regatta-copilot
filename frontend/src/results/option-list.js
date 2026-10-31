// The route options as selectable cards: name, type, chance of being the best, arrival gap.

import { createTermTip } from "./term-tip.js";
import { formatNumber } from "./display-format.js";
import { element } from "../dom.js";

export class OptionList {
  constructor(container, translator, onSelect) {
    this.container = container;
    this.translator = translator;
    this.onSelect = onSelect;
  }

  render(result, selectedId) {
    const heading = element("h2", "section-title");
    heading.append(this.translator.t("options.title"), createTermTip(this.translator, "tip.probability"));
    const list = element("ul", "option-list");
    result.options.forEach((option, index) => {
      list.append(this.#card(result, option, index, option.id === selectedId));
    });
    this.container.replaceChildren(heading, list);
  }

  #card(result, option, index, selected) {
    const t = (key, params) => this.translator.t(key, params);
    const item = element("li");
    const button = element("button", "option-card");
    button.type = "button";
    button.dataset.route = String(index + 1);
    button.setAttribute("aria-pressed", String(selected));
    button.addEventListener("click", () => this.onSelect(option.id));

    const header = element("span", "option-header");
    header.append(element("span", "option-swatch"), element("span", "option-name", t(`option.name.${option.id}`)));
    if (option.id === result.recommended_option) header.append(element("span", "badge", t("option.recommended")));

    const percent = Math.round(option.probability * 100);
    const meter = element("span", "option-meter");
    meter.style.setProperty("--share", `${percent}%`);

    button.append(
      header,
      element("span", "option-kind", t(`option.kind.${option.kind}`)),
      element("span", "option-probability", t("option.probability", { percent })),
      meter,
      element("span", "option-detail", t("option.members", { count: option.member_count, total: result.weather.member_count })),
      element("span", "option-detail", option.eta_delta_h === 0
        ? t("option.eta_best")
        : t("option.eta_delta", {
          hours: formatNumber(option.eta_delta_h, this.translator.lang, Number.isInteger(option.eta_delta_h) ? 0 : 1),
        })),
    );
    if (option.game_route) button.append(element("span", "option-game", t("option.game_route")));
    item.append(button);
    return item;
  }
}
