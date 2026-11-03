// Message shown when newer weather has arrived since the shown routes were computed: the player enters the boat's
// current position from the game and computes again.

import { element } from "../dom.js";

export class WeatherUpdateNotice {
  #visible = false;

  constructor(container, translator, onEnterPosition) {
    this.container = container;
    this.translator = translator;
    this.onEnterPosition = onEnterPosition;
    this.render();
  }

  show() {
    this.#visible = true;
    this.render();
  }

  hide() {
    this.#visible = false;
    this.render();
  }

  render() {
    this.container.hidden = !this.#visible;
    if (!this.#visible) return;
    const button = element("button", "chip", this.translator.t("weather_update.enter_position"));
    button.type = "button";
    button.addEventListener("click", () => this.onEnterPosition());
    this.container.replaceChildren(element("span", "", this.translator.t("weather_update.message")), button);
  }
}
