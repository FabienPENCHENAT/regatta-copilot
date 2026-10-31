// Controls of the chart: map view (next 24 h, 48 h, 5 days or whole race), the time bar (hour shown), wind as
// particles or barbs, and the wind colour legend in knots. The time bar is kept across renders (see TimeBar).

import { WIND_MODES } from "./route-map.js";
import { WIND_COLOR_TOKENS } from "./map-style.js";
import { TimeBar } from "./time-bar.js";
import { createTermTip } from "../results/term-tip.js";
import { element } from "../dom.js";

export const MAP_VIEWS = ["day", "near", "five", "race"];
const LEGEND_KNOTS = [0, 5, 10, 15, 20, 25, "30+"];

export class MapControls {
  constructor(container, translator, { onSelectView, onSelectHour, onSelectMode }) {
    this.container = container;
    this.translator = translator;
    this.onSelectView = onSelectView;
    this.onSelectMode = onSelectMode;
    this.timeBar = new TimeBar(translator, onSelectHour);
    this.viewSlot = element("div");
    this.modeSlot = element("div");
    this.legendSlot = element("div");
    container.replaceChildren(this.viewSlot, this.timeBar.element, this.modeSlot, this.legendSlot);
  }

  // timeline: { maxHour, marks, startIso } of the selected option.
  render({ view, hour, windMode, timeline }) {
    const t = (key, params) => this.translator.t(key, params);
    this.viewSlot.replaceChildren(this.#group(t("view.label"),
      MAP_VIEWS.map((v) => this.#toggle(t(`view.${v}`), v === view, () => this.onSelectView(v)))));
    this.timeBar.update({ hour, ...timeline });
    const modeGroup = this.#group(t("wind.mode_label"),
      WIND_MODES.map((m) => this.#toggle(t(`wind.mode_${m}`), m === windMode, () => this.onSelectMode(m))));
    modeGroup.append(createTermTip(this.translator, "tip.barbs"));
    this.modeSlot.replaceChildren(modeGroup);
    this.legendSlot.replaceChildren(this.#legend());
  }

  retranslate() {
    this.timeBar.retranslate();
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
