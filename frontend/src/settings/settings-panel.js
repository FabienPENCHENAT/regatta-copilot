// The settings dialog: opened from the rail, it holds the boat options (sails, foils, hull, pro winch), the
// editable manoeuvre times (pre-filled from the boat's polar for the winch level) and the polar import.
// Any change recomputes.

import { BoatOptionsForm } from "./boat-options-form.js";
import { ManeuverTimes } from "./maneuver-times.js";
import { PolarImport } from "./polar-import.js";

export class SettingsPanel {
  #boatId = null;
  #polar = null;

  constructor(dialog, openButton, { api, translator, preferences, onChange, onPolarChange }) {
    openButton.addEventListener("click", () => dialog.showModal());
    this.maneuvers = new ManeuverTimes(dialog.querySelector("#maneuver-times"), { translator, preferences, onChange });
    this.polarImport = new PolarImport(dialog.querySelector("#polar-import"), { api, translator, onChange: onPolarChange });
    this.boat = new BoatOptionsForm(dialog, {
      preferences,
      onChange: (options) => {
        this.#loadManeuvers(); // the pro winch changes the game's manoeuvre times
        onChange(options);
      },
    });
  }

  // What the backend needs for a computation.
  get request() {
    return { options: this.boat.options, maneuvers: this.maneuvers.values };
  }

  ownedSails() {
    return this.boat.ownedSails();
  }

  showPolar(raceId, boatId, polar) {
    this.#boatId = boatId;
    this.#polar = polar;
    this.#loadManeuvers();
    this.polarImport.render(raceId, boatId, polar);
  }

  retranslate() {
    this.maneuvers.render();
  }

  #loadManeuvers() {
    if (this.#boatId) this.maneuvers.load(this.#boatId, this.#polar?.winch, this.boat.options.pro_winch);
  }
}
