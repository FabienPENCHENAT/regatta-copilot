// Position typed as in the game: degrees, minutes, seconds and a hemisphere button, for latitude then longitude.
// Number fields open the numeric keypad and move to the next field once full (or on space, °, ', "); pasting a
// whole position in any field fills them all. The position is also kept as text (47°30'00"N 006°45'00"W) for the
// saved preferences.

import { element } from "../dom.js";

const AXES = {
  lat: { hemispheres: ["N", "S"], maxDeg: 90, degDigits: 2 },
  lon: { hemispheres: ["W", "E"], maxDeg: 180, degDigits: 3 },
};
const PARTS = [
  { key: "deg", unit: "°" },
  { key: "min", unit: "'", digits: 2 },
  { key: "sec", unit: '"', digits: 2 },
];
const NEXT_FIELD_KEYS = [" ", "°", "'", '"', "Enter"];

export class PositionFields {
  #inputs = { lat: {}, lon: {} };
  #hemisphere = { lat: "N", lon: "W" };
  #hemisphereButtons = {};

  constructor(container, { translator, parser, onChange }) {
    this.container = container;
    this.translator = translator;
    this.parser = parser;
    this.onChange = onChange;
    this.#render();
  }

  // { lat, lon } in decimal degrees, or null while a field is empty or out of range.
  get value() {
    const lat = this.#axisValue("lat");
    const lon = this.#axisValue("lon");
    return lat === null || lon === null ? null : { lat, lon };
  }

  get isEmpty() {
    return this.#allInputs().every((input) => input.value.trim() === "");
  }

  get text() {
    const position = this.value;
    if (!position) return "";
    return `${this.#axisText("lat")} ${this.#axisText("lon")}`;
  }

  setText(text) {
    const position = this.parser.parse(text);
    if (position) this.#fill(position);
  }

  focus() {
    (this.#allInputs().find((input) => input.getAttribute("aria-invalid") === "true") ?? this.#inputs.lat.deg).focus();
  }

  retranslate() {
    for (const axis of Object.keys(AXES)) {
      this.#inputs[axis].label.textContent = this.translator.t(`form.${axis}`);
      for (const { key } of PARTS) {
        this.#inputs[axis][key].setAttribute("aria-label", `${this.translator.t(`form.${axis}`)} — ${this.translator.t(`form.${key}`)}`);
      }
      this.#renderHemisphere(axis);
    }
  }

  #render() {
    const rows = Object.keys(AXES).map((axis) => {
      const row = element("div", "position-row");
      const label = element("span", "position-axis");
      this.#inputs[axis].label = label;
      row.append(label);
      for (const part of PARTS) {
        const input = element("input", "position-part");
        Object.assign(input, { type: "text", inputMode: part.key === "sec" ? "decimal" : "numeric", autocomplete: "off" });
        input.dataset.part = part.key;
        input.maxLength = part.key === "sec" ? 5 : part.digits ?? AXES[axis].degDigits;
        this.#bindInput(input, axis, part);
        this.#inputs[axis][part.key] = input;
        const cell = element("span", "position-cell");
        cell.append(input, element("span", "position-unit", part.unit));
        row.append(cell);
      }
      const button = element("button", "position-hemisphere");
      button.type = "button";
      button.addEventListener("click", () => this.#toggleHemisphere(axis));
      this.#hemisphereButtons[axis] = button;
      row.append(button);
      return row;
    });
    this.container.replaceChildren(...rows);
    this.retranslate();
  }

  #bindInput(input, axis, part) {
    input.addEventListener("keydown", (event) => {
      if (NEXT_FIELD_KEYS.includes(event.key)) {
        event.preventDefault();
        this.#next(input)?.focus();
      }
    });
    input.addEventListener("paste", (event) => {
      const position = this.parser.parse(event.clipboardData.getData("text"));
      if (!position) return;
      event.preventDefault();
      this.#fill(position);
      this.#changed();
    });
    input.addEventListener("input", () => {
      input.value = input.value.replace(part.key === "sec" ? /[^\d.,]/g : /\D/g, "");
      const full = (part.digits ?? AXES[axis].degDigits) <= input.value.length && !/[.,]/.test(input.value);
      if (full && part.key !== "sec") this.#next(input)?.focus();
      this.#changed();
    });
    input.addEventListener("focus", () => input.select());
  }

  #next(input) {
    const inputs = this.#allInputs();
    return inputs[inputs.indexOf(input) + 1];
  }

  #allInputs() {
    return ["lat", "lon"].flatMap((axis) => PARTS.map(({ key }) => this.#inputs[axis][key]));
  }

  #toggleHemisphere(axis) {
    const [first, second] = AXES[axis].hemispheres;
    this.#hemisphere[axis] = this.#hemisphere[axis] === first ? second : first;
    this.#renderHemisphere(axis);
    this.#changed();
  }

  #renderHemisphere(axis) {
    const button = this.#hemisphereButtons[axis];
    button.textContent = this.translator.t(`form.hemisphere.${this.#hemisphere[axis]}`);
    button.setAttribute("aria-label", this.translator.t("form.hemisphere_toggle", {
      current: this.translator.t(`form.hemisphere_name.${this.#hemisphere[axis]}`),
    }));
  }

  #fill(position) {
    for (const axis of Object.keys(AXES)) {
      const value = position[axis];
      this.#hemisphere[axis] = value < 0 ? AXES[axis].hemispheres.find((h) => h === "S" || h === "W")
        : AXES[axis].hemispheres.find((h) => h === "N" || h === "E");
      let seconds = Math.round(Math.abs(value) * 3600);
      const deg = Math.floor(seconds / 3600);
      seconds -= deg * 3600;
      const inputs = this.#inputs[axis];
      inputs.deg.value = String(deg).padStart(AXES[axis].degDigits, "0");
      inputs.min.value = String(Math.floor(seconds / 60)).padStart(2, "0");
      inputs.sec.value = String(seconds % 60).padStart(2, "0");
      this.#renderHemisphere(axis);
    }
  }

  #axisValue(axis) {
    const parts = PARTS.map(({ key }) => this.#number(this.#inputs[axis][key]));
    const [deg, min, sec] = parts;
    const valid = parts.every((n) => n !== null) && min < 60 && sec < 60;
    const value = valid ? deg + min / 60 + sec / 3600 : null;
    return value !== null && value <= AXES[axis].maxDeg
      ? (["S", "W"].includes(this.#hemisphere[axis]) ? -value : value) : null;
  }

  #number(input) {
    const text = input.value.trim().replace(",", ".");
    return text === "" || Number.isNaN(Number(text)) ? null : Number(text);
  }

  #axisText(axis) {
    const { deg, min, sec } = this.#inputs[axis];
    const degDigits = AXES[axis].degDigits;
    return `${deg.value.padStart(degDigits, "0")}°${min.value.padStart(2, "0")}'${sec.value.padStart(2, "0")}"${this.#hemisphere[axis]}`;
  }

  #changed() {
    for (const axis of Object.keys(AXES)) {
      const invalid = this.#axisValue(axis) === null;
      for (const { key } of PARTS) {
        const input = this.#inputs[axis][key];
        const n = this.#number(input);
        const wrong = input.value !== "" && (n === null || (key !== "deg" && n >= 60) || (key === "deg" && n > AXES[axis].maxDeg));
        input.setAttribute("aria-invalid", String(wrong || (invalid && input.value === "" && !this.isEmpty)));
      }
    }
    this.onChange();
  }
}
