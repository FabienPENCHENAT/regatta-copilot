// Loads a language file and turns i18n keys into text. All UI text goes through this class.

export const SUPPORTED_LANGUAGES = ["fr", "en"];

export class Translator {
  #messages = {};
  #lang = "fr";

  get lang() {
    return this.#lang;
  }

  async load(lang) {
    const response = await fetch(`i18n/${lang}.json`);
    if (!response.ok) throw new Error(`Cannot load language file ${lang}`);
    this.#messages = await response.json();
    this.#lang = lang;
    document.documentElement.lang = lang;
  }

  // A param may itself be a translatable reference: { key: "direction.west" }.
  t(key, params = {}) {
    const template = this.#messages[key] ?? key;
    return template.replace(/\{(\w+)\}/g, (match, name) => {
      const value = params[name];
      if (value === undefined) return match;
      return typeof value === "object" && value.key ? this.t(value.key, value.params) : String(value);
    });
  }

  // Fills every element marked with data-i18n (text) or data-i18n-attr ("attr:key;attr:key").
  applyTo(root) {
    root.querySelectorAll("[data-i18n]").forEach((el) => {
      el.textContent = this.t(el.dataset.i18n);
    });
    root.querySelectorAll("[data-i18n-attr]").forEach((el) => {
      for (const pair of el.dataset.i18nAttr.split(";")) {
        const [attr, key] = pair.split(":");
        el.setAttribute(attr, this.t(key));
      }
    });
  }

  static detectBrowserLanguage() {
    const preferred = (navigator.language || "fr").slice(0, 2).toLowerCase();
    return SUPPORTED_LANGUAGES.includes(preferred) ? preferred : "en";
  }
}
