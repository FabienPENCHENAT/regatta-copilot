// The settings dialog: opened from the rail, it holds the owned sails and the editable manoeuvre times
// (pre-filled from the boat's polar). Any change asks for a new computation.

import { BoatOptionsForm } from "./boat-options-form.js";
import { ManeuverTimes } from "./maneuver-times.js";

export class SettingsPanel {
  constructor(dialog, openButton, { translator, preferences, onChange }) {
    openButton.addEventListener("click", () => dialog.showModal());
    this.sails = new BoatOptionsForm(dialog, { preferences, onChange });
    this.maneuvers = new ManeuverTimes(dialog.querySelector("#maneuver-times"), { translator, preferences, onChange });
  }

  // What the backend needs for a computation.
  get request() {
    return { options: this.sails.options, maneuvers: this.maneuvers.values };
  }

  ownedSails() {
    return this.sails.ownedSails();
  }

  showPolar(boatId, polar) {
    this.maneuvers.load(boatId, polar?.winch);
  }

  retranslate() {
    this.maneuvers.render();
  }
}
