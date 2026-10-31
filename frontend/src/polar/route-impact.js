// "On your route": the game's route computed with the current options and with the tried ones, from the last
// position typed on the map page; shows the miles gained at +24 h, +48 h and +120 h.

import { element } from "../dom.js";
import { formatCoordinates } from "../results/display-format.js";

export class RouteImpact {
  #request = 0;

  constructor(container, { api, translator }) {
    this.container = container;
    this.api = api;
    this.translator = translator;
    this.button = container.querySelector("[data-impact-run]");
    this.output = container.querySelector("[data-impact-output]");
  }

  // context: { raceId, boatId, position, maneuvers, current, changed, changedAnything }
  bind(getContext) {
    this.getContext = getContext;
    this.button.addEventListener("click", () => this.#measure());
  }

  // Options changed: the last figures no longer apply.
  clear() {
    this.#request += 1;
    this.button.disabled = false;
    this.output.replaceChildren();
  }

  render() {
    const { position, changedAnything } = this.getContext();
    this.button.textContent = this.translator.t("polar.impact.button");
    this.button.disabled = !position || !changedAnything;
    if (!position) this.output.replaceChildren(element("p", "polar-note", this.translator.t("polar.impact.no_position")));
  }

  async #measure() {
    const context = this.getContext();
    const request = ++this.#request;
    this.button.disabled = true;
    this.output.replaceChildren(element("p", "polar-note", this.translator.t("polar.impact.running")));
    try {
      const result = await this.api.compareOptions(context);
      if (request !== this.#request) return;
      this.output.replaceChildren(this.#tiles(result.gains), element("p", "polar-note", this.translator.t(
        "polar.impact.from", { position: formatCoordinates(context.position) })));
    } catch (error) {
      if (request !== this.#request) return;
      this.output.replaceChildren(element("p", "polar-note error", this.translator.t("polar.impact.error", { reason: error.message })));
    } finally {
      if (request === this.#request) this.button.disabled = false;
    }
  }

  #tiles(gains) {
    const list = element("ul", "polar-impact-tiles");
    for (const { hours, gain_nm: gain } of gains) {
      const tile = element("li", gain > 0.05 ? "gain" : gain < -0.05 ? "loss" : "even");
      const value = gain.toLocaleString(this.translator.lang, { maximumFractionDigits: 1, signDisplay: "exceptZero" });
      tile.append(element("strong", "", this.translator.t("polar.impact.miles", { value })),
        element("span", "", this.translator.t("polar.impact.at", { hours })));
      list.append(tile);
    }
    return list;
  }
}
