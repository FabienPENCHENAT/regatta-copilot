// Controls under the chart: map view (next 48 h or whole race), hour shown (start, +4 h ... +48 h),
// wind as particles or barbs, and the wind colour legend in knots.

import { WIND_MODES } from "./route-map.js";
import { WIND_COLOR_TOKENS } from "./map-style.js";
import { createTermTip } from "../results/term-tip.js";
import { element } from "../dom.js";

export const MAP_VIEWS = ["near", "race"];
const LEGEND_KNOTS = [0, 5, 10, 15, 20, 25, "30+"];

export class MapControls {
  constructor(container, translator, { onSelectView, onSelectHour, onSelectMode }) {
    this.container = container;
    this.translator = translator;
    this.onSelectView = onSelectView;
    this.onSelectHour = onSelectHour;
    this.onSelectMode = onSelectMode;
  }

  render({ view, hours, hour, windMode }) {
    const t = (key, params) => this.translator.t(key, params);
    const viewGroup = this.#group(t("view.label"),
      MAP_VIEWS.map((v) => this.#toggle(t(`view.${v}`), v === view, () => this.onSelectView(v))));
    const timeGroup = this.#group(t("wind.time_label"),
      hours.map((h) => this.#toggle(h === 0 ? t("wind.time_start") : t("wind.time_plus", { h }), h === hour,
        () => this.onSelectHour(h))));
    const modeGroup = this.#group(t("wind.mode_label"),
      WIND_MODES.map((m) => this.#toggle(t(`wind.mode_${m}`), m === windMode, () => this.onSelectMode(m))));
    modeGroup.append(createTermTip(this.translator, "tip.barbs"));
    this.container.replaceChildren(viewGroup, timeGroup, modeGroup, this.#legend());
  }

  #group(label, buttons) {
    const group = element("div", "chip-group");
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
