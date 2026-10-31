// The three inputs (race, boat, position) and the "Compute my route" button.
// Reports a valid position as soon as it is typed, so the map can show it before computing.

import { formatCoordinates } from "../results/display-format.js";

export class RouteForm {
  #races = [];
  #position = null;

  constructor({ form, raceSelect, boatSelect, positionInput, positionFeedback, submitButton }, deps) {
    Object.assign(this, { form, raceSelect, boatSelect, positionInput, positionFeedback, submitButton });
    this.translator = deps.translator;
    this.parser = deps.parser;
    this.onPositionChange = deps.onPositionChange;
    this.onSubmit = deps.onSubmit;
    this.onSelectionChange = deps.onSelectionChange;
    this.#bindEvents();
  }

  setRaces(races, { raceId, boatId } = {}) {
    this.#races = races;
    this.#fillRaceOptions(raceId);
    this.#fillBoatOptions(boatId);
  }

  setPositionText(text) {
    this.positionInput.value = text;
    this.#readPosition();
  }

  retranslate() {
    this.#fillRaceOptions(this.raceSelect.value);
    this.#fillBoatOptions(this.boatSelect.value);
    this.#readPosition();
  }

  showProgress(done, total) {
    this.submitButton.disabled = true;
    this.submitButton.textContent = this.translator.t("form.computing", { done, total });
  }

  showIdle() {
    this.submitButton.disabled = false;
    this.submitButton.textContent = this.translator.t("form.submit");
  }

  #bindEvents() {
    this.raceSelect.addEventListener("change", () => {
      this.#fillBoatOptions();
      this.#notifySelection();
    });
    this.boatSelect.addEventListener("change", () => this.#notifySelection());
    this.positionInput.addEventListener("input", () => this.#readPosition());
    this.form.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!this.#readPosition()) return this.positionInput.focus();
      this.onSubmit({ raceId: this.raceSelect.value, boatId: this.boatSelect.value, position: this.#position });
    });
  }

  #fillRaceOptions(selectedId) {
    this.raceSelect.replaceChildren(
      ...this.#races.map((race) => this.#option(race.id, `race.${race.id}`, race.id === selectedId)),
    );
  }

  #fillBoatOptions(selectedId) {
    const race = this.#races.find((r) => r.id === this.raceSelect.value) ?? this.#races[0];
    const chosen = race.boats.includes(selectedId) ? selectedId : race.default_boat;
    this.boatSelect.replaceChildren(...race.boats.map((id) => this.#option(id, `boat.${id}`, id === chosen)));
  }

  #option(value, key, selected) {
    return new Option(this.translator.t(key), value, selected, selected);
  }

  #readPosition() {
    const text = this.positionInput.value;
    this.#position = this.parser.parse(text);
    const valid = this.#position !== null;
    this.positionInput.setAttribute("aria-invalid", String(!valid && text.trim() !== ""));
    this.positionFeedback.dataset.state = valid ? "ok" : text.trim() ? "error" : "empty";
    this.positionFeedback.textContent = valid
      ? this.translator.t("form.position_ok", { coords: formatCoordinates(this.#position) })
      : text.trim()
        ? this.translator.t("form.position_error")
        : this.translator.t("form.position_hint");
    this.onPositionChange(this.#position);
    return valid;
  }

  #notifySelection() {
    this.onSelectionChange({ raceId: this.raceSelect.value, boatId: this.boatSelect.value });
  }
}
