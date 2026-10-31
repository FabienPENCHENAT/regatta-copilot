// Time bar of the chart: a slider over the whole route with stops every hour for the first day, then every 3 h
// (the GFS steps, and the route points beyond +48 h); a mark for each change of orders of the selected option,
// snapped to a stop; two buttons jumping to the previous / next change. The slider moves stop by stop, the
// first day taking as much room as its 24 stops. Built once and updated in place, so a drag is never cut.

import { element } from "../dom.js";
import { formatLocalTime } from "../results/display-format.js";

const DAY_H = 24;
const HOURLY_UNTIL_H = 24;
const COARSE_STEP_H = 3;

// Hours the slider can show: 0, 1 … 24, 27, 30 … up to `maxHour`.
export function timeStops(maxHour) {
  const stops = [];
  for (let hour = 0; hour <= Math.min(maxHour, HOURLY_UNTIL_H); hour += 1) stops.push(hour);
  for (let hour = HOURLY_UNTIL_H + COARSE_STEP_H; hour <= maxHour; hour += COARSE_STEP_H) stops.push(hour);
  return stops;
}

export class TimeBar {
  #hour = 0;
  #marks = [];
  #stops = [0];
  #startIso = null;

  constructor(translator, onSelectHour) {
    this.translator = translator;
    this.onSelectHour = onSelectHour;
    this.element = element("div", "time-bar");
    this.#build();
  }

  // hour: shown hour; maxHour: end of the route; marks: hours where the orders change; startIso: route start.
  update({ hour, maxHour, marks, startIso }) {
    this.#hour = hour;
    this.#startIso = startIso;
    const snapped = [...new Set(marks.map((mark) => this.#stopAtOrBefore(mark, timeStops(maxHour))))].filter((h) => h > 0);
    if (this.#stops.at(-1) !== maxHour || String(snapped) !== String(this.#marks)) {
      this.#stops = timeStops(maxHour);
      this.slider.max = String(this.#stops.length - 1);
      this.#marks = snapped;
      this.#drawScale();
    }
    const index = String(this.#stops.indexOf(this.#stopAtOrBefore(hour, this.#stops)));
    if (this.slider.value !== index) this.slider.value = index;
    this.#renderLabels();
  }

  retranslate() {
    this.title.textContent = this.translator.t("wind.time_label");
    this.previous.setAttribute("aria-label", this.translator.t("timebar.previous"));
    this.next.setAttribute("aria-label", this.translator.t("timebar.next"));
    this.slider.setAttribute("aria-label", this.translator.t("wind.time_label"));
    this.#drawScale();
    this.#renderLabels();
  }

  #build() {
    const head = element("div", "time-bar-head");
    this.title = element("span", "time-bar-title");
    this.value = element("span", "time-bar-value");
    head.append(this.title, this.value);
    this.previous = this.#arrow("M15 6l-6 6 6 6", () => this.#jump(-1));
    this.next = this.#arrow("M9 6l6 6-6 6", () => this.#jump(1));
    this.slider = element("input", "time-bar-slider");
    Object.assign(this.slider, { type: "range", min: "0", max: "120", step: "1", value: "0" });
    this.slider.addEventListener("input", () => this.onSelectHour(this.#stops[Number(this.slider.value)]));
    this.track = element("div", "time-bar-track");
    this.track.append(this.slider);
    this.scale = element("div", "time-bar-scale");
    this.track.append(this.scale);
    const row = element("div", "time-bar-row");
    row.append(this.previous, this.track, this.next);
    this.element.append(head, row);
    this.retranslate();
  }

  #arrow(path, onClick) {
    const button = element("button", "time-bar-arrow");
    button.type = "button";
    button.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${path}"/></svg>`;
    button.addEventListener("click", onClick);
    return button;
  }

  // Order marks above the line, day labels below it.
  #drawScale() {
    const maxHour = this.#stops.at(-1);
    if (!maxHour) return;
    const at = (hour) => `${(this.#stops.indexOf(hour) / (this.#stops.length - 1)) * 100}%`;
    const marks = this.#marks.map((hour) => {
      const mark = element("span", "time-bar-mark");
      mark.style.left = at(hour);
      return mark;
    });
    const days = [];
    for (let hour = 0; hour <= maxHour; hour += DAY_H) {
      const edge = hour === 0 ? " first" : hour + DAY_H > maxHour ? " last" : "";
      const label = element("span", `time-bar-day${edge}`,
        hour === 0 ? this.translator.t("wind.time_start") : this.translator.t("timebar.day", { d: hour / DAY_H }));
      label.style.left = at(hour);
      days.push(label);
    }
    this.scale.replaceChildren(...marks, ...days);
  }

  #renderLabels() {
    const offset = this.#hour === 0 ? this.translator.t("wind.time_start") : this.translator.t("wind.time_plus", { h: this.#hour });
    this.value.textContent = this.#startIso
      ? `${offset} · ${formatLocalTime(this.#startIso, this.#hour, this.translator.lang)}` : offset;
    this.previous.disabled = this.#hour <= 0;
    this.next.disabled = this.#hour >= this.#stops.at(-1);
  }

  #jump(direction) {
    const max = this.#stops.at(-1);
    const target = direction > 0
      ? this.#marks.find((hour) => hour > this.#hour) ?? max
      : this.#marks.findLast((hour) => hour < this.#hour) ?? 0;
    this.onSelectHour(target);
  }

  #stopAtOrBefore(hour, stops) {
    return stops.findLast((stop) => stop <= hour) ?? 0;
  }
}
