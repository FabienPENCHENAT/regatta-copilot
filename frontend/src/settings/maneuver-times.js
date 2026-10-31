// Editable manoeuvre times: for a tack, a gybe and a sail change, how long the boat slows down in light and
// strong wind and the speed it keeps meanwhile. Pre-filled from the boat's VR polar for the winch level owned
// (standard or pro); the player's own values are saved per boat and winch level and sent with each
// computation. "Game values" resets them.

import { element } from "../dom.js";

const MANEUVERS = [
  { key: "tack", label: "settings.tack" },
  { key: "gybe", label: "settings.gybe" },
  { key: "sailChange", label: "settings.sail_change" },
];
const FIELDS = [
  { key: "light_min", label: "settings.light_wind", step: 0.5, unit: "settings.minutes_short" },
  { key: "strong_min", label: "settings.strong_wind", step: 0.5, unit: "settings.minutes_short" },
  { key: "speed_percent", label: "settings.kept_speed", step: 5, unit: "settings.percent" },
];

export class ManeuverTimes {
  #gameValues = null;
  #values = null;
  #storageKey = null;

  constructor(container, { translator, preferences, onChange }) {
    this.container = container;
    this.translator = translator;
    this.preferences = preferences;
    this.onChange = onChange;
  }

  // The values to send to the backend (all three manoeuvres), or {} before the polar is known.
  get values() {
    return this.#values ?? {};
  }

  load(boatId, winch, proWinch) {
    const level = proWinch ? "pro" : "std";
    this.#storageKey = `${boatId}:${level}`;
    this.#gameValues = winch ? gameValues(winch, level) : null;
    const saved = this.preferences.read().maneuvers?.[this.#storageKey];
    this.#values = saved ?? structuredClone(this.#gameValues);
    this.render();
  }

  render() {
    if (!this.#values) return;
    const t = (key, params) => this.translator.t(key, params);
    const head = element("div", "maneuver-row maneuver-head");
    head.append(element("span"), ...FIELDS.map((field) => element("span", "", t(field.label))));
    const rows = MANEUVERS.map(({ key, label }) => {
      const row = element("div", "maneuver-row");
      row.append(element("span", "maneuver-name", t(label)), ...FIELDS.map((field) => this.#input(key, field)));
      return row;
    });
    const reset = element("button", "text-button", t("settings.game_values"));
    reset.type = "button";
    reset.addEventListener("click", () => this.#reset());
    const note = element("p", "fine-print", t("settings.maneuver_note"));
    this.container.replaceChildren(head, ...rows, note, reset);
  }

  #input(maneuver, field) {
    const t = (key) => this.translator.t(key);
    const label = element("label", "maneuver-input");
    const input = element("input");
    Object.assign(input, { type: "number", min: 0, step: field.step, value: this.#values[maneuver][field.key] });
    input.setAttribute("aria-label", `${t(MANEUVERS.find((m) => m.key === maneuver).label)} · ${t(field.label)}`);
    input.addEventListener("change", () => {
      this.#values[maneuver][field.key] = Math.max(0, Number(input.value) || 0);
      this.#save();
    });
    label.append(input, element("span", "", t(field.unit)));
    return label;
  }

  #reset() {
    this.#values = structuredClone(this.#gameValues);
    this.#save(true);
    this.render();
  }

  #save(isReset = false) {
    const all = { ...this.preferences.read().maneuvers };
    if (isReset) delete all[this.#storageKey];
    else all[this.#storageKey] = this.#values;
    this.preferences.update({ maneuvers: all });
    this.onChange(this.values);
  }
}

function gameValues(winch, level) {
  return Object.fromEntries(MANEUVERS.map(({ key }) => {
    const { lw, hw } = winch[key][level];
    return [key, { light_min: lw.timer / 60, strong_min: hw.timer / 60, speed_percent: Math.round(lw.ratio * 100) }];
  }));
}
