// FR/EN toggle in the header. Tells the app when the user picks another language.

import { SUPPORTED_LANGUAGES } from "./translator.js";

export class LanguagePicker {
  constructor(container, onChange) {
    this.container = container;
    this.onChange = onChange;
  }

  render(currentLang) {
    this.container.replaceChildren(
      ...SUPPORTED_LANGUAGES.map((lang) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "lang-button";
        button.textContent = lang.toUpperCase();
        button.lang = lang;
        button.setAttribute("aria-pressed", String(lang === currentLang));
        button.addEventListener("click", () => this.onChange(lang));
        return button;
      }),
    );
  }
}
