// The sails part of the settings: which optional VR sails the player owns, one by one. Saved in the browser
// and sent with each computation. Jib and Spi are always on board. Foils, hull and pro winch are not used:
// the routing gives directions from the sails and the boat's polar only.

const BASE_SAILS = ["Jib", "Spi"];
const OPTIONAL_SAILS = ["LightJib", "LightGnk", "Staysail", "HeavyGnk", "Code0"];

export class BoatOptionsForm {
  constructor(container, { preferences, onChange }) {
    this.preferences = preferences;
    this.onChange = onChange;
    this.boxes = Object.fromEntries(OPTIONAL_SAILS.map((s) => [s, container.querySelector(`[data-sail="${s}"]`)]));
    const owned = preferences.read().boatOptions?.sails ?? [];
    for (const [sail, box] of Object.entries(this.boxes)) {
      box.checked = owned.includes(sail);
      box.addEventListener("change", () => this.#save());
    }
  }

  // The shape the API expects: { sails: [...] }.
  get options() {
    return { sails: OPTIONAL_SAILS.filter((sail) => this.boxes[sail].checked) };
  }

  ownedSails() {
    return [...BASE_SAILS, ...this.options.sails];
  }

  #save() {
    this.preferences.update({ boatOptions: this.options });
    this.onChange(this.options);
  }
}
