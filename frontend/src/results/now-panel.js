// "Set this now" for the selected option, as boat instruments side by side: a compass (heading and wind
// direction), the sail wardrobe with the sail to hoist, a true-wind gauge, a speed dial, then the advice sentence.

import { describeTwa, formatHeading } from "./display-format.js";
import { createTermTip } from "./term-tip.js";
import { createCompassDial } from "./instruments/compass-dial.js";
import { createSailWardrobe } from "./instruments/sail-wardrobe.js";
import { createWindGauge } from "./instruments/wind-gauge.js";
import { createSpeedGauge } from "./instruments/speed-gauge.js";
import { colourSlot } from "./option-places.js";
import { element } from "../dom.js";

const CARDINAL_KEYS = ["compass.n", "compass.e", "compass.s", "compass.w"];

export class NowPanel {
  constructor(container, translator) {
    this.container = container;
    this.translator = translator;
  }

  render(result, option, ownedSails) {
    const t = (key, params) => this.translator.t(key, params);
    const now = option.now;
    const title = element("h2", "panel-title now-title", t("now.title"));
    const optionName = element("span", "now-option", t(`option.name.${option.id}`));
    optionName.style.setProperty("--route", `var(--route-${colourSlot(option.id)})`);
    title.append(optionName);

    const instruments = element("div", "instruments");
    instruments.append(this.#headingCell(now), this.#sailCell(now, ownedSails), this.#windCell(now), this.#speedCell(now));
    const advice = element("p", "advice", t(result.advice.key,
      { ...result.advice.params, direction: { key: `direction.${result.advice.params.option}` } }));
    this.container.replaceChildren(title, instruments, advice);
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
        twaDeg: now.twa_deg,
      }),
      element("span", "heading-value", formatHeading(now.heading_deg)),
      element("span", "gauge-caption", `${t("label.twa")} ${twa.angle} ${t(twa.tackKey)}`),
    );
    return cell;
  }

  #sailCell(now, ownedSails) {
    const cell = this.#cell("instrument-sail", "label.sail");
    cell.append(createSailWardrobe(this.translator, now.sail, ownedSails));
    return cell;
  }

  #windCell(now) {
    const cell = this.#cell("instrument-wind", "label.tws", "tip.tws");
    cell.append(createWindGauge(this.translator, now.tws_kn));
    return cell;
  }

  #speedCell(now) {
    const cell = this.#cell("instrument-speed", "label.speed");
    cell.append(createSpeedGauge(this.translator, now.speed_kn));
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
