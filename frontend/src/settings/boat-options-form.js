// The "Boat options" part of the settings: which VR options the player owns, sail by sail, plus foils,
// polished hull and pro winch. Saved in the browser and sent with each computation.

const BASE_SAILS = ["Jib", "Spi"];
const OPTIONAL_SAILS = ["LightJib", "LightGnk", "Staysail", "HeavyGnk", "Code0"];
const EQUIPMENT = ["foil", "hull", "pro_winch"];
const DEFAULTS = { sails: [], foil: true, hull: false, pro_winch: false };

export class BoatOptionsForm {
  constructor(container, { preferences, onChange }) {
    this.preferences = preferences;
    this.onChange = onChange;
    this.sailBoxes = Object.fromEntries(OPTIONAL_SAILS.map((s) => [s, container.querySelector(`[data-sail="${s}"]`)]));
    this.equipmentBoxes = Object.fromEntries(EQUIPMENT.map((e) => [e, container.querySelector(`[data-equipment="${e}"]`)]));
    const saved = { ...DEFAULTS, ...preferences.read().boatOptions };
    for (const [sail, box] of Object.entries(this.sailBoxes)) box.checked = (saved.sails ?? []).includes(sail);
    for (const [item, box] of Object.entries(this.equipmentBoxes)) box.checked = Boolean(saved[item]);
    for (const box of [...Object.values(this.sailBoxes), ...Object.values(this.equipmentBoxes)]) {
      box.addEventListener("change", () => this.#save());
    }
  }

  // The shape the API expects: { sails: [...], foil, hull, pro_winch }.
  get options() {
    const sails = OPTIONAL_SAILS.filter((sail) => this.sailBoxes[sail].checked);
    return { sails, ...Object.fromEntries(EQUIPMENT.map((item) => [item, this.equipmentBoxes[item].checked])) };
  }

  ownedSails() {
    return [...BASE_SAILS, ...this.options.sails];
  }

  #save() {
    this.preferences.update({ boatOptions: this.options });
    this.onChange(this.options);
  }
}
