// Route plan of one option at +4/8/12/16/24/48 h: target position, heading, sail, wind, confidence.

import { confidenceLevel, describeTwa, formatCoordinates, formatHeading, formatKnots, formatLocalTime } from "./display-format.js";
import { labelWithTip } from "./term-tip.js";
import { element } from "../dom.js";

const COLUMNS = [
  { key: "label.when" },
  { key: "label.position" },
  { key: "label.heading", tip: "tip.heading" },
  { key: "label.sail" },
  { key: "label.twa", tip: "tip.twa" },
  { key: "label.tws", tip: "tip.tws" },
  { key: "label.speed" },
  { key: "label.confidence", tip: "tip.confidence" },
];

export class TimelineTable {
  constructor(container, translator) {
    this.container = container;
    this.translator = translator;
  }

  render(result, option) {
    const t = (key, params) => this.translator.t(key, params);
    const title = element("h2", "section-title", t("timeline.title", { option: t(`option.name.${option.id}`) }));
    const table = element("table", "timeline");
    table.append(element("caption", "", t("timeline.caption")), this.#head());
    const body = element("tbody");
    option.steps.forEach((step) => body.append(this.#row(result, step)));
    table.append(body);
    const scroller = element("div", "timeline-scroller");
    scroller.append(table);
    this.container.replaceChildren(title, scroller);
  }

  #head() {
    const head = element("thead");
    const row = element("tr");
    for (const column of COLUMNS) {
      const th = element("th");
      th.scope = "col";
      th.append(column.tip ? labelWithTip(this.translator, column.key, column.tip) : this.translator.t(column.key));
      row.append(th);
    }
    head.append(row);
    return head;
  }

  #row(result, step) {
    const t = (key, params) => this.translator.t(key, params);
    const twa = describeTwa(step.twa_deg);
    const level = confidenceLevel(step.confidence);
    const when = element("th");
    when.scope = "row";
    when.append(
      element("span", "when-hours", t("timeline.in_hours", { h: step.hour })),
      element("span", "when-time", formatLocalTime(result.computed_at, step.hour, this.translator.lang)),
    );
    const confidence = element("span", "pill", `${Math.round(step.confidence * 100)} % · ${t(`confidence.${level}`)}`);
    confidence.dataset.level = level;

    const row = element("tr");
    row.append(
      when,
      this.#cell("label.position", formatCoordinates(step), "coords"),
      this.#cell("label.heading", formatHeading(step.heading_deg), "strong"),
      this.#cell("label.sail", t(`sail.${step.sail}`), "strong"),
      this.#cell("label.twa", `${twa.angle} ${t(twa.tackKey)}`),
      this.#cell("label.tws", formatKnots(step.tws_kn, this.translator)),
      this.#cell("label.speed", formatKnots(step.speed_kn, this.translator)),
      this.#cell("label.confidence", confidence),
    );
    return row;
  }

  // data-label lets the CSS show each cell as "label: value" on narrow screens.
  #cell(labelKey, content, className = "") {
    const td = element("td", className);
    td.dataset.label = this.translator.t(labelKey);
    td.append(content);
    return td;
  }
}
