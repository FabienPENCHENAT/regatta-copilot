// Entry point of the "How it works" page: language and theme as on the map page, then the sections.

import { Translator } from "./i18n/translator.js";
import { LanguagePicker } from "./i18n/language-picker.js";
import { PreferencesStore } from "./storage/preferences-store.js";
import { HowPage } from "./how/how-page.js";

const preferences = new PreferencesStore();
const saved = preferences.read();
if (saved.theme) document.documentElement.dataset.theme = saved.theme;

const translator = new Translator();
const page = new HowPage(document.getElementById("how-sections"), translator);
const picker = new LanguagePicker(document.getElementById("lang-picker"), (lang) => show(lang));

async function show(lang) {
  await translator.load(lang);
  preferences.update({ lang });
  translator.applyTo(document.body);
  document.title = `${translator.t("how.title")} · ${translator.t("app.title")}`;
  picker.render(lang);
  page.render();
}

show(saved.lang ?? Translator.detectBrowserLanguage());
