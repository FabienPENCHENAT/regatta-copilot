// Time bar of the chart: a slider over the whole route (hour by hour), a mark for each change of orders of the
// selected option, and two buttons jumping to the previous / next change. Built once and updated in place, so
// a drag is never interrupted by a redraw.

import { element } from "../dom.js";
import { formatLocalTime } from "../results/display-format.js";

const DAY_H = 24;

export class TimeBar {
  #hour = 0;
  #marks = [];
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
    if (Number(this.slider.max) !== maxHour || String(marks) !== String(this.#marks)) {
      this.slider.max = String(maxHour);
      this.#marks = marks;
      this.#drawScale(maxHour);
    }
    if (Number(this.slider.value) !== hour) this.slider.value = String(hour);
    this.#renderLabels();
  }

  retranslate() {
    this.title.textContent = this.translator.t("wind.time_label");
    this.previous.setAttribute("aria-label", this.translator.t("timebar.previous"));
    this.next.setAttribute("aria-label", this.translator.t("timebar.next"));
    this.slider.setAttribute("aria-label", this.translator.t("wind.time_label"));
    this.#drawScale(Number(this.slider.max));
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
    this.slider.addEventListener("input", () => this.onSelectHour(Number(this.slider.value)));
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
  #drawScale(maxHour) {
    if (!maxHour) return;
    const at = (hour) => `${(hour / maxHour) * 100}%`;
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
    this.next.disabled = this.#hour >= Number(this.slider.max);
  }

  #jump(direction) {
    const max = Number(this.slider.max);
    const target = direction > 0
      ? this.#marks.find((hour) => hour > this.#hour) ?? max
      : this.#marks.findLast((hour) => hour < this.#hour) ?? 0;
    this.onSelectHour(target);
  }
}
