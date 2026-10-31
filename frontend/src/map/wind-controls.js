// Controls under the chart: which hour to show (start, +4 h ... +48 h), particles or barbs,
// and the wind colour legend in knots.

import { WIND_MODES } from "./route-map.js";
import { WIND_COLOR_TOKENS } from "./map-style.js";
import { createTermTip } from "../results/term-tip.js";
import { element } from "../dom.js";

const LEGEND_KNOTS = [0, 5, 10, 15, 20, 25, "30+"];

export class WindControls {
  constructor(container, translator, { onSelectHour, onSelectMode }) {
    this.container = container;
    this.translator = translator;
    this.onSelectHour = onSelectHour;
    this.onSelectMode = onSelectMode;
  }

  render(hours, selectedHour, mode) {
    const t = (key, params) => this.translator.t(key, params);
    const timeGroup = this.#group("wind-times", t("wind.time_label"),
      hours.map((h) => this.#toggle(h === 0 ? t("wind.time_start") : t("wind.time_plus", { h }), h === selectedHour,
        () => this.onSelectHour(h))));
    const modeGroup = this.#group("wind-modes", t("wind.mode_label"),
      WIND_MODES.map((m) => this.#toggle(t(`wind.mode_${m}`), m === mode, () => this.onSelectMode(m))));
    modeGroup.append(createTermTip(this.translator, "tip.barbs"));
    this.container.replaceChildren(timeGroup, modeGroup, this.#legend());
  }

  #group(className, label, buttons) {
    const group = element("div", `chip-group ${className}`);
    group.setAttribute("role", "group");
    group.setAttribute("aria-label", label);
    group.append(...buttons);
    return group;
  }

  #toggle(label, pressed, onClick) {
    const button = element("button", "chip", label);
    button.type = "button";
    button.setAttribute("aria-pressed", String(pressed));
    button.addEventListener("click", onClick);
    return button;
  }

  #legend() {
    const legend = element("div", "wind-legend");
    legend.append(element("span", "wind-legend-title", this.translator.t("wind.legend")));
    const scale = element("span", "wind-legend-scale");
    WIND_COLOR_TOKENS.forEach((token, i) => {
      const swatch = element("span", "wind-legend-step", String(LEGEND_KNOTS[i]));
      swatch.style.setProperty("--swatch", `var(${token})`);
      scale.append(swatch);
    });
    legend.append(scale);
    return legend;
  }
}
