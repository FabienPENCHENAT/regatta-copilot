// The "Boat options" part of the settings: which VR options the player owns. Saved in the browser and sent
// with each computation. Jib and Spi are always on board; option packs add sails.

export const OPTION_NAMES = ["light", "heavy", "reach", "foil", "hull", "pro_winch"];
const DEFAULT_OPTIONS = { light: false, heavy: false, reach: false, foil: true, hull: false, pro_winch: false };
const SAILS_BY_PACK = { light: ["LightJib", "LightGnk"], heavy: ["Staysail", "HeavyGnk"], reach: ["Code0"] };
const BASE_SAILS = ["Jib", "Spi"];

export class BoatOptionsForm {
  constructor(container, { preferences, onChange }) {
    this.preferences = preferences;
    this.onChange = onChange;
    this.checkboxes = Object.fromEntries(
      OPTION_NAMES.map((name) => [name, container.querySelector(`[data-option="${name}"]`)]),
    );
    const saved = { ...DEFAULT_OPTIONS, ...preferences.read().boatOptions };
    for (const [name, box] of Object.entries(this.checkboxes)) {
      box.checked = Boolean(saved[name]);
      box.addEventListener("change", () => this.#save());
    }
  }

  get options() {
    return Object.fromEntries(OPTION_NAMES.map((name) => [name, this.checkboxes[name].checked]));
  }

  ownedSails() {
    const options = this.options;
    return [...BASE_SAILS, ...Object.entries(SAILS_BY_PACK).filter(([pack]) => options[pack]).flatMap(([, sails]) => sails)];
  }

  #save() {
    this.preferences.update({ boatOptions: this.options });
    this.onChange(this.options);
  }
}
