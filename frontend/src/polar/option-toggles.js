// The game's options as toggle chips: optional sails one by one, foils, polished hull, pro winch. Starts from the
// player's settings, marks what the settings own, and reports every change.

import { element } from "../dom.js";

const OPTIONAL_SAILS = ["LightJib", "LightGnk", "Staysail", "HeavyGnk", "Code0"];
const EQUIPMENT = [["foil", "settings.foils"], ["hull", "settings.hull"], ["pro_winch", "settings.winch"]];

export class OptionToggles {
  #owned;
  #tried;

  constructor(container, { translator, owned, onChange }) {
    this.container = container;
    this.translator = translator;
    this.onChange = onChange;
    this.#owned = normalise(owned);
    this.#tried = normalise(owned);
  }

  // The options in the shape the API expects: { sails: [...], foil, hull, pro_winch }.
  get owned() {
    return structuredClone(this.#owned);
  }

  get tried() {
    return structuredClone(this.#tried);
  }

  get changed() {
    return JSON.stringify(this.#owned) !== JSON.stringify(this.#tried);
  }

  reset() {
    this.#tried = structuredClone(this.#owned);
    this.render();
    this.onChange();
  }

  // The tried options become the player's own (after "keep them in my settings").
  adopt() {
    this.#owned = structuredClone(this.#tried);
    this.render();
  }

  render() {
    const sails = OPTIONAL_SAILS.map((sail) => this.#chip(this.translator.t(`sail.${sail}`), sail,
      this.#tried.sails.includes(sail), this.#owned.sails.includes(sail), () => this.#toggleSail(sail)));
    const equipment = EQUIPMENT.map(([key, label]) => this.#chip(this.translator.t(label), null,
      this.#tried[key], this.#owned[key], () => this.#toggleEquipment(key)));
    this.container.replaceChildren(
      this.#group("settings.sails", sails), this.#group("settings.equipment", equipment));
  }

  #group(titleKey, chips) {
    const group = element("div", "polar-option-group");
    const list = element("div", "polar-chips");
    list.append(...chips);
    group.append(element("h3", "polar-option-title", this.translator.t(titleKey)), list);
    return group;
  }

  #chip(label, sail, pressed, owned, toggle) {
    const button = element("button", "polar-chip");
    button.type = "button";
    button.setAttribute("aria-pressed", String(pressed));
    if (sail) {
      const swatch = element("span", "polar-swatch");
      swatch.style.background = `var(--sail-${sail})`;
      button.append(swatch);
    }
    button.append(element("span", "", label));
    if (owned) button.append(element("span", "polar-owned", this.translator.t("polar.owned")));
    button.addEventListener("click", toggle);
    return button;
  }

  #toggleSail(sail) {
    const sails = new Set(this.#tried.sails);
    if (sails.has(sail)) sails.delete(sail);
    else sails.add(sail);
    this.#tried = { ...this.#tried, sails: OPTIONAL_SAILS.filter((s) => sails.has(s)) };
    this.render();
    this.onChange();
  }

  #toggleEquipment(key) {
    this.#tried = { ...this.#tried, [key]: !this.#tried[key] };
    this.render();
    this.onChange();
  }
}

function normalise(options = {}) {
  return {
    sails: OPTIONAL_SAILS.filter((sail) => (options.sails ?? []).includes(sail)),
    foil: Boolean(options.foil), hull: Boolean(options.hull), pro_winch: Boolean(options.pro_winch),
  };
}
