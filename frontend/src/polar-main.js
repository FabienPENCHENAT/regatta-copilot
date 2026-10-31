// Entry point of the "Polar and options" page: language and theme as on the map page, then the page.

import { ApiClient } from "./api/api-client.js";
import { Translator } from "./i18n/translator.js";
import { LanguagePicker } from "./i18n/language-picker.js";
import { PreferencesStore } from "./storage/preferences-store.js";
import { PolarPage } from "./polar/polar-page.js";

const byId = (id) => document.getElementById(id);
const preferences = new PreferencesStore();
const saved = preferences.read();
if (saved.theme) document.documentElement.dataset.theme = saved.theme;

const translator = new Translator();
const page = new PolarPage({
  boat: byId("polar-boat"), boats: byId("polar-boats"), chart: byId("polar-chart"), tws: byId("polar-tws"), twsValue: byId("polar-tws-value"),
  twa: byId("polar-twa"), twaValue: byId("polar-twa-value"), readout: byId("polar-readout"), legend: byId("polar-legend"),
  toggles: byId("polar-toggles"), summary: byId("polar-summary"), reset: byId("polar-reset"), keep: byId("polar-keep"),
  kept: byId("polar-kept"), impact: byId("polar-impact"),
}, { api: new ApiClient(), translator, preferences });
const picker = new LanguagePicker(byId("lang-picker"), (lang) => show(lang));
let started = false;

async function show(lang) {
  await translator.load(lang);
  preferences.update({ lang });
  translator.applyTo(document.body);
  document.title = `${translator.t("polar.title")} · ${translator.t("app.title")}`;
  picker.render(lang);
  if (started) page.render();
  else {
    started = true;
    await page.start();
  }
}

show(saved.lang ?? Translator.detectBrowserLanguage());
