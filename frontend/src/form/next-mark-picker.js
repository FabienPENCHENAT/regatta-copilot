// "Next mark" choice in the race card: automatic (the server detects the gates already crossed) or a mark
// picked by the player, needed around Guadeloupe where a position alone cannot tell which buoys are rounded.

const AUTO = "auto";

export class NextMarkPicker {
  #marks = [];
  #detected = null;

  constructor(select, { translator, preferences, onChange }) {
    this.select = select;
    this.translator = translator;
    this.preferences = preferences;
    select.addEventListener("change", () => {
      this.preferences.update({ nextMark: this.value });
      onChange(this.value);
    });
  }

  // null = automatic; otherwise a mark id.
  get value() {
    return this.select.value === AUTO ? null : this.select.value;
  }

  render(race, selected = this.preferences.read().nextMark ?? null) {
    this.#marks = [...race.marks.map((mark) => mark.id), "finish"];
    this.#fill(selected);
  }

  // After a computation: shows which mark the automatic choice used.
  showDetected(markId) {
    this.#detected = markId;
    this.#fill(this.value);
  }

  retranslate() {
    if (this.#marks.length) this.#fill(this.value);
  }

  #fill(selected) {
    const t = (key) => this.translator.t(key);
    const autoLabel = this.#detected ? `${t("form.next_mark_auto")} · ${t(`mark.${this.#detected}`)}` : t("form.next_mark_auto");
    const options = [new Option(autoLabel, AUTO, !selected, !selected)];
    for (const id of this.#marks) options.push(new Option(t(`mark.${id}`), id, id === selected, id === selected));
    this.select.replaceChildren(...options);
  }
}
