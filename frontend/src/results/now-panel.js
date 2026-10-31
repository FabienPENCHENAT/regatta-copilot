// "Set this now" for the selected option, as boat instruments: a compass (heading and wind direction),
// the sail wardrobe with the sail to hoist, a true-wind gauge and a speed dial, then the advice sentence.

import { describeTwa, formatHeading } from "./display-format.js";
import { createTermTip } from "./term-tip.js";
import { createCompassDial } from "./instruments/compass-dial.js";
import { createSailWardrobe } from "./instruments/sail-wardrobe.js";
import { createWindGauge } from "./instruments/wind-gauge.js";
import { createSpeedGauge } from "./instruments/speed-gauge.js";
import { element } from "../dom.js";

const CARDINAL_KEYS = ["compass.n", "compass.e", "compass.s", "compass.w"];

export class NowPanel {
  constructor(container, translator) {
    this.container = container;
    this.translator = translator;
  }

  render(result, option) {
    const t = (key, params) => this.translator.t(key, params);
    const now = option.now;
    const head = element("div", "panel-head");
    head.append(element("h2", "panel-title", t("now.title")),
      element("span", "panel-subtitle", t("now.for_option", { option: t(`option.name.${option.id}`) })));

    const instruments = element("div", "instruments");
    instruments.append(this.#headingCell(now), this.#sailCell(now), this.#windAndSpeedCell(now));
    const advice = element("p", "advice", t(result.advice.key,
      { ...result.advice.params, direction: { key: `direction.${result.advice.params.option}` } }));
    this.container.replaceChildren(head, instruments, advice);
  }

  #headingCell(now) {
    const t = (key, params) => this.translator.t(key, params);
    const twa = describeTwa(now.twa_deg);
    const cell = this.#cell("instrument-heading", "label.heading", "tip.heading");
    cell.append(
      createCompassDial({
        headingDeg: now.heading_deg,
        windFromDeg: (now.heading_deg + now.twa_deg + 360) % 360,
        cardinals: CARDINAL_KEYS.map((key) => t(key)),
      }),
      element("span", "heading-value", formatHeading(now.heading_deg)),
      element("span", "gauge-caption", `${t("label.twa")} ${twa.angle} ${t(twa.tackKey)}`),
    );
    return cell;
  }

  #sailCell(now) {
    const cell = this.#cell("instrument-sail", "label.sail");
    cell.append(createSailWardrobe(this.translator, now.sail));
    return cell;
  }

  #windAndSpeedCell(now) {
    const cell = element("div", "instrument instrument-gauges");
    const wind = this.#cell("", "label.tws", "tip.tws");
    wind.append(createWindGauge(this.translator, now.tws_kn));
    const speed = this.#cell("", "label.speed");
    speed.append(createSpeedGauge(this.translator, now.speed_kn));
    cell.append(wind, speed);
    return cell;
  }

  #cell(className, labelKey, tipKey = null) {
    const cell = element("div", `instrument ${className}`.trim());
    const label = element("span", "instrument-label", this.translator.t(labelKey));
    if (tipKey) label.append(createTermTip(this.translator, tipKey));
    cell.append(label);
    return cell;
  }
}
