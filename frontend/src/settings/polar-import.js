// "Boat polar" part of the settings: says which polar the computation uses (community copy or the player's
// own export from the game), imports a JSON file copied from the game, and goes back to the community polar.

import { element } from "../dom.js";

export class PolarImport {
  #target = null; // { raceId, boatId }

  constructor(container, { api, translator, onChange }) {
    this.container = container;
    this.api = api;
    this.translator = translator;
    this.onChange = onChange;
  }

  render(raceId, boatId, polar, message = null) {
    this.#target = { raceId, boatId };
    const t = (key, params) => this.translator.t(key, params);
    const fromPlayer = polar?._source === "player";
    const status = element("p", "fine-print", fromPlayer
      ? t("settings.polar_player", { date: new Date(polar._imported_at).toLocaleString(this.translator.lang) })
      : t("settings.polar_current"));
    const actions = element("div", "polar-actions");
    actions.append(this.#fileButton());
    if (fromPlayer) actions.append(this.#resetButton());
    const children = [status, actions];
    if (message) children.push(element("p", `polar-message ${message.kind}`, message.text));
    this.container.replaceChildren(...children);
  }

  #fileButton() {
    const label = element("label", "file-button");
    const input = element("input");
    Object.assign(input, { type: "file", accept: "application/json,.json,.txt" });
    input.addEventListener("change", () => input.files[0] && this.#import(input.files[0]));
    label.append(input, element("span", "", this.translator.t("settings.polar_import")));
    return label;
  }

  #resetButton() {
    const button = element("button", "text-button", this.translator.t("settings.polar_reset"));
    button.type = "button";
    button.addEventListener("click", () => this.#run(() => this.api.resetPolar(this.#target), "settings.polar_reset_done"));
    return button;
  }

  async #import(file) {
    let polar;
    try {
      polar = JSON.parse(await file.text());
    } catch {
      return this.#refresh({ kind: "error", text: this.translator.t("settings.polar_not_json") });
    }
    return this.#run(() => this.api.importPolar(this.#target, polar), "settings.polar_import_done");
  }

  async #run(action, doneKey) {
    try {
      await action();
      await this.#refresh({ kind: "ok", text: this.translator.t(doneKey) });
      this.onChange();
    } catch (error) {
      await this.#refresh({ kind: "error", text: this.translator.t("settings.polar_refused", { reason: error.message }) });
    }
  }

  async #refresh(message) {
    const { raceId, boatId } = this.#target;
    const polar = await this.api.getPolar(raceId, boatId).catch(() => null);
    this.render(raceId, boatId, polar, message);
  }
}
