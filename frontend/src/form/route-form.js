// The race card inputs: race, boat (pills), position, and the "Compute my route" button.
// Reports a valid position as soon as it is typed, so the map can show it before computing, and keeps a
// one-line summary for when the card is collapsed.

import { BoatPicker } from "./boat-picker.js";
import { formatCoordinates } from "../results/display-format.js";

export class RouteForm {
  #races = [];
  #position = null;

  constructor({ form, raceSelect, boatPicker, positionInput, positionFeedback, submitButton, summary }, deps) {
    Object.assign(this, { form, raceSelect, positionInput, positionFeedback, submitButton, summary });
    this.translator = deps.translator;
    this.parser = deps.parser;
    this.onPositionChange = deps.onPositionChange;
    this.onSubmit = deps.onSubmit;
    this.onSelectionChange = deps.onSelectionChange;
    this.boats = new BoatPicker(boatPicker, this.translator, () => this.#selectionChanged());
    this.#bindEvents();
  }

  get raceId() {
    return this.raceSelect.value;
  }

  get boatId() {
    return this.boats.value;
  }

  setRaces(races, { raceId, boatId } = {}) {
    this.#races = races;
    this.#fillRaceOptions(raceId);
    this.#renderBoats(boatId);
  }

  setPositionText(text) {
    this.positionInput.value = text;
    this.#readPosition();
  }

  retranslate() {
    this.#fillRaceOptions(this.raceId);
    this.#renderBoats(this.boatId);
    this.#readPosition();
  }

  showProgress(done, total) {
    this.submitButton.disabled = true;
    this.submitButton.querySelector(".submit-label").textContent = this.translator.t("form.computing", { done, total });
  }

  showIdle() {
    this.submitButton.disabled = false;
    this.submitButton.querySelector(".submit-label").textContent = this.translator.t("form.submit");
  }

  #bindEvents() {
    this.raceSelect.addEventListener("change", () => {
      this.#renderBoats();
      this.#selectionChanged();
    });
    this.positionInput.addEventListener("input", () => this.#readPosition());
    this.form.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!this.#readPosition()) return this.positionInput.focus();
      this.onSubmit({ raceId: this.raceId, boatId: this.boatId, position: this.#position });
    });
  }

  #fillRaceOptions(selectedId) {
    this.raceSelect.replaceChildren(...this.#races.map((race) =>
      new Option(this.translator.t(`race.${race.id}`), race.id, race.id === selectedId, race.id === selectedId)));
  }

  #renderBoats(selectedId) {
    const race = this.#races.find((r) => r.id === this.raceId) ?? this.#races[0];
    this.boats.render(race.boats, race.boats.includes(selectedId) ? selectedId : race.default_boat);
  }

  #readPosition() {
    const text = this.positionInput.value;
    this.#position = this.parser.parse(text);
    const valid = this.#position !== null;
    this.positionInput.setAttribute("aria-invalid", String(!valid && text.trim() !== ""));
    this.positionInput.parentElement.classList.toggle("valid", valid);
    this.positionFeedback.dataset.state = valid ? "ok" : text.trim() ? "error" : "empty";
    this.positionFeedback.textContent = valid
      ? this.translator.t("form.position_ok", { coords: formatCoordinates(this.#position) })
      : text.trim()
        ? this.translator.t("form.position_error")
        : this.translator.t("form.position_hint");
    this.onPositionChange(this.#position);
    this.#renderSummary();
    return valid;
  }

  #renderSummary() {
    const boat = this.translator.t(`boat.${this.boatId}`);
    const position = this.#position ? formatCoordinates(this.#position) : "—";
    this.summary.textContent = this.translator.t("form.summary", { boat, position });
  }

  #selectionChanged() {
    this.#renderSummary();
    this.onSelectionChange({ raceId: this.raceId, boatId: this.boatId });
  }
}
