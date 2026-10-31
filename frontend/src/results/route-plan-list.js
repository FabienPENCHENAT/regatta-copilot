// Route plan of the selected option at +4/8/12/16/24/48 h, as a compact list: when, heading and sail,
// wind and speed, target position, and a confidence bar. Tapping a step shows that hour on the map.

import { confidenceLevel, describeTwa, formatCoordinates, formatHeading, formatKnots, formatLocalTime } from "./display-format.js";
import { createTermTip } from "./term-tip.js";
import { element } from "../dom.js";

export class RoutePlanList {
  constructor(container, translator, onSelectHour) {
    this.container = container;
    this.translator = translator;
    this.onSelectHour = onSelectHour;
  }

  render(result, option, selectedHour) {
    const t = (key, params) => this.translator.t(key, params);
    const head = element("div", "panel-head");
    const title = element("h2", "panel-title", t("timeline.title", { option: t(`option.name.${option.id}`) }));
    title.append(createTermTip(this.translator, "tip.confidence"));
    head.append(title, element("span", "panel-subtitle", t("timeline.caption")));
    const list = element("ol", "plan-list");
    option.steps.forEach((step) => list.append(this.#step(result, step, step.hour === selectedHour)));
    this.container.replaceChildren(head, list);
  }

  #step(result, step, selected) {
    const t = (key, params) => this.translator.t(key, params);
    const twa = describeTwa(step.twa_deg);
    const level = confidenceLevel(step.confidence);
    const item = element("li");
    const button = element("button", "plan-step");
    button.type = "button";
    button.setAttribute("aria-pressed", String(selected));
    button.title = t("timeline.show_on_map");
    button.addEventListener("click", () => this.onSelectHour(step.hour));

    const when = element("span", "plan-when");
    when.append(element("span", "plan-hours", t("wind.time_plus", { h: step.hour })),
      element("span", "plan-time", formatLocalTime(result.computed_at, step.hour, this.translator.lang)));

    const main = element("span", "plan-main");
    main.append(
      element("span", "plan-order", `${formatHeading(step.heading_deg)} · ${t(`sail.${step.sail}`)}`),
      element("span", "plan-wind", `${t("label.tws")} ${formatKnots(step.tws_kn, this.translator)} · ${t("label.twa")} ${twa.angle} ${t(twa.tackKey)} · ${formatKnots(step.speed_kn, this.translator)}`),
      element("span", "plan-position", formatCoordinates(step)),
    );

    const confidence = element("span", "plan-confidence");
    confidence.dataset.level = level;
    const bar = element("span", "confidence-bar");
    bar.style.setProperty("--share", `${Math.round(step.confidence * 100)}%`);
    confidence.append(bar, element("span", "confidence-value", `${Math.round(step.confidence * 100)} %`));
    confidence.setAttribute("aria-label", `${t("label.confidence")} ${t(`confidence.${level}`)}`);

    button.append(when, main, confidence);
    item.append(button);
    return item;
  }
}
