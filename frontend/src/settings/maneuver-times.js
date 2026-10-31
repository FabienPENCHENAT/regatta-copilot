// Read-only manoeuvre times taken from the boat's VR polar (winch block): for a tack, a gybe and a sail
// change, how long the boat slows down and to what share of its speed, in light (≤ lws) and strong (≥ hws)
// wind, with or without the pro winch. The routing engine uses the same figures.

import { element } from "../dom.js";

const MANEUVERS = [
  { key: "tack", label: "settings.tack" },
  { key: "gybe", label: "settings.gybe" },
  { key: "sailChange", label: "settings.sail_change" },
];

export class ManeuverTimes {
  constructor(container, translator) {
    this.container = container;
    this.translator = translator;
  }

  render(winch, proWinch) {
    if (!winch) return;
    const level = proWinch ? "pro" : "std";
    const rows = MANEUVERS.map(({ key, label }) => {
      const { lw, hw } = winch[key][level];
      const row = element("div", "maneuver-row");
      row.append(
        element("span", "maneuver-name", this.translator.t(label)),
        element("span", "maneuver-figures", this.translator.t("settings.maneuver_figures", {
          light: minutes(lw.timer), strong: minutes(hw.timer), percent: Math.round(lw.ratio * 100),
          lost_light: minutes(lw.timer * (1 - lw.ratio)), lost_strong: minutes(hw.timer * (1 - hw.ratio)),
        })),
      );
      return row;
    });
    const note = element("p", "fine-print", this.translator.t("settings.maneuver_note", { lws: winch.lws, hws: winch.hws }));
    this.container.replaceChildren(...rows, note);
  }
}

function minutes(seconds) {
  const whole = Math.floor(seconds / 60);
  const rest = Math.round(seconds % 60);
  return rest ? `${whole} min ${String(rest).padStart(2, "0")}` : `${whole} min`;
}
