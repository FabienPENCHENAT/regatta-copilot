// Boat class choice as a row of pills (a radio group), instead of a drop-down list.

import { element } from "../dom.js";

export class BoatPicker {
  #value = null;

  constructor(container, translator, onChange) {
    this.container = container;
    this.translator = translator;
    this.onChange = onChange;
  }

  get value() {
    return this.#value;
  }

  render(boatIds, selectedId) {
    this.#value = selectedId;
    this.container.replaceChildren(...boatIds.map((id) => this.#pill(id)));
  }

  #pill(id) {
    const label = element("label", "boat-pill");
    const input = element("input");
    Object.assign(input, { type: "radio", name: "boat", value: id, checked: id === this.#value });
    input.addEventListener("change", () => {
      this.#value = id;
      this.onChange(id);
    });
    label.append(input, element("span", "", this.translator.t(`boat.${id}`)));
    return label;
  }
}
