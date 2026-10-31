// The settings dialog: opened from the rail, it holds the owned boat options and the manoeuvre times
// read from the boat's polar.

import { BoatOptionsForm } from "./boat-options-form.js";
import { ManeuverTimes } from "./maneuver-times.js";

export class SettingsPanel {
  #winch = null;

  constructor(dialog, openButton, { translator, preferences, onOptionsChange }) {
    openButton.addEventListener("click", () => dialog.showModal());
    this.maneuvers = new ManeuverTimes(dialog.querySelector("#maneuver-times"), translator);
    this.boatOptions = new BoatOptionsForm(dialog, {
      preferences,
      onChange: (options) => {
        this.#renderManeuvers();
        onOptionsChange(options);
      },
    });
  }

  get options() {
    return this.boatOptions.options;
  }

  ownedSails() {
    return this.boatOptions.ownedSails();
  }

  showPolar(polar) {
    this.#winch = polar?.winch ?? null;
    this.#renderManeuvers();
  }

  retranslate() {
    this.#renderManeuvers();
  }

  #renderManeuvers() {
    this.maneuvers.render(this.#winch, this.options.pro_winch);
  }
}
