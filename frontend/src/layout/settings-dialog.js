// Opens the settings dialog from the rail. The dialog's own form closes it.

export class SettingsDialog {
  constructor(openButton, dialog) {
    openButton.addEventListener("click", () => dialog.showModal());
  }
}
