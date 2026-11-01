// Boat speed on a half-dial, like a log on a chart table: arc from 0 to the scale maximum, needle on the value.

import { formatNumber } from "../display-format.js";
import { element } from "../../dom.js";

const SCALE_MAX_KN = 30; // above the Class40 (18.6 kn) and IMOCA speeds; faster boats peg the needle at the end
const RADIUS = 46;
const ARC_LENGTH = Math.PI * RADIUS;
const SCALE_GAP = 19; // 0 and max labels sit this far below the arc ends, clear of the thick arc

export function createSpeedGauge(translator, speedKn) {
  const share = Math.min(speedKn / SCALE_MAX_KN, 1);
  const needle = -90 + share * 180;
  const gauge = element("div", "speed-gauge");
  gauge.innerHTML = `<svg viewBox="-60 -56 120 ${66 + SCALE_GAP - 10}" aria-hidden="true">
    <path class="speed-track" d="M${-RADIUS} 0 A${RADIUS} ${RADIUS} 0 0 1 ${RADIUS} 0"/>
    <path class="speed-value" d="M${-RADIUS} 0 A${RADIUS} ${RADIUS} 0 0 1 ${RADIUS} 0"
      stroke-dasharray="${(ARC_LENGTH * share).toFixed(1)} ${ARC_LENGTH.toFixed(1)}"/>
    <line class="speed-needle" x1="0" y1="0" x2="0" y2="${-RADIUS + 10}" transform="rotate(${needle.toFixed(1)})"/>
    <circle class="speed-hub" r="4"/>
    <text class="speed-scale" x="${-RADIUS}" y="${SCALE_GAP}">0</text>
    <text class="speed-scale" x="${RADIUS}" y="${SCALE_GAP}">${SCALE_MAX_KN}</text>
  </svg>`;
  const value = element("span", "gauge-value", formatNumber(speedKn, translator.lang));
  value.append(element("span", "gauge-unit", translator.t("unit.knots_symbol")));
  gauge.append(value, element("span", "gauge-caption", translator.t("now.speed_detail")));
  return gauge;
}
