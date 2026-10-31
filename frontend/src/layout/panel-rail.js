// Left icon rail: each button shows or hides one floating panel so the chart can be seen in full,
// and the gear opens the settings dialog.

export class PanelRail {
  constructor(rail, { settingsButton, settingsDialog, onLayoutChange }) {
    this.buttons = [...rail.querySelectorAll("[data-panel]")];
    this.onLayoutChange = onLayoutChange;
    for (const button of this.buttons) {
      button.setAttribute("aria-pressed", "true");
      button.addEventListener("click", () => this.#toggle(button));
    }
    settingsButton.addEventListener("click", () => settingsDialog.showModal());
  }

  #toggle(button) {
    const panel = document.getElementById(button.dataset.panel);
    const visible = panel.hidden;
    panel.hidden = !visible;
    button.setAttribute("aria-pressed", String(visible));
    this.onLayoutChange();
  }
}
