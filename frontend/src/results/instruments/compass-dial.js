// Compass rose with the boat pointing at its heading, the sail to hoist seen from above (leeward, eased with the
// wind angle) and an arrow on the rim showing where the wind comes from (pointing at the centre, the way the
// wind blows), so the angle to the wind and the trim are visible at a glance. Angles in degrees, 0 = north.

import { sailTopViewPath } from "./sail-top-view.js";

const RIM = 70;

export function createCompassDial({ headingDeg, windFromDeg, cardinals, sail, twaDeg }) {
  const ticks = Array.from({ length: 36 }, (_, i) => {
    const major = i % 3 === 0;
    return `<line class="dial-tick${major ? " major" : ""}" x1="0" y1="${-RIM}" x2="0" y2="${-RIM + (major ? 9 : 5)}"
      transform="rotate(${i * 10})"/>`;
  }).join("");
  const letters = cardinals.map((label, i) => {
    const angle = (i * Math.PI) / 2;
    return `<text class="dial-cardinal" x="${(52 * Math.sin(angle)).toFixed(1)}" y="${(-52 * Math.cos(angle) + 4).toFixed(1)}">${label}</text>`;
  }).join("");

  const sailPath = sailTopViewPath(sail, twaDeg);
  const wrapper = document.createElement("div");
  wrapper.className = "compass-dial";
  wrapper.innerHTML = `<svg viewBox="-94 -94 188 188" aria-hidden="true">
    <circle class="dial-face" r="${RIM}"/>
    ${ticks}${letters}
    <line class="dial-course" x1="0" y1="0" x2="0" y2="${-RIM}" transform="rotate(${headingDeg})"/>
    <g transform="rotate(${windFromDeg})">
      <path class="dial-wind" d="M0 ${-RIM - 4} L8 ${-RIM - 17} L2.5 ${-RIM - 17} L2.5 ${-RIM - 28} L-2.5 ${-RIM - 28} L-2.5 ${-RIM - 17} L-8 ${-RIM - 17} Z"/>
    </g>
    <g transform="rotate(${headingDeg})">
      <path class="dial-boat" d="M0 -30 C9 -16 10 6 7 24 L-7 24 C-10 6 -9 -16 0 -30 Z"/>
      ${sailPath ? `<path class="dial-sail" d="${sailPath}"/>` : ""}
    </g>
  </svg>`;
  return wrapper;
}
