// True wind strength on a 0–40 kn bar painted with the same colours as the wind on the map,
// with the Beaufort force in words.

import { beaufortForce } from "./beaufort.js";
import { formatNumber } from "../display-format.js";
import { element } from "../../dom.js";

const SCALE_MAX_KN = 40;

export function createWindGauge(translator, speedKn) {
  const force = beaufortForce(speedKn);
  const gauge = element("div", "wind-gauge");
  const value = element("span", "gauge-value", formatNumber(speedKn, translator.lang));
  value.append(element("span", "gauge-unit", translator.t("unit.knots_symbol")));
  const bar = element("span", "wind-bar");
  bar.style.setProperty("--position", `${Math.min(speedKn / SCALE_MAX_KN, 1) * 100}%`);
  bar.append(element("span", "wind-bar-marker"));
  const scale = element("span", "wind-bar-scale");
  scale.append(element("span", "", "0"), element("span", "", "20"), element("span", "", "40"));
  gauge.append(value, bar, scale,
    element("span", "gauge-caption", translator.t("beaufort.label", { force, name: translator.t(`beaufort.${force}`) })));
  return gauge;
}
