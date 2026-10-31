// Entry point: creates the components, connects them, and keeps the current result and selection.

import { Translator } from "./i18n/translator.js";
import { LanguagePicker } from "./i18n/language-picker.js";
import { PreferencesStore } from "./storage/preferences-store.js";
import { PositionParser } from "./form/position-parser.js";
import { RouteForm } from "./form/route-form.js";
import { RouteMap } from "./map/route-map.js";
import { NowPanel } from "./results/now-panel.js";
import { OptionList } from "./results/option-list.js";
import { TimelineTable } from "./results/timeline-table.js";
import { formatUtcHour } from "./results/display-format.js";
import { MockApi } from "./api/mock-api.js";

const SAMPLE_POSITION_TEXT = `47°30'00"N 006°45'00"W`;

class App {
  #result = null;
  #selectedOptionId = null;

  constructor() {
    this.api = new MockApi();
    this.preferences = new PreferencesStore();
    this.translator = new Translator();
    this.languagePicker = new LanguagePicker(byId("lang-picker"), (lang) => this.changeLanguage(lang));
    this.map = new RouteMap(byId("map"), this.translator);
    this.nowPanel = new NowPanel(byId("now-panel"), this.translator);
    this.optionList = new OptionList(byId("options"), this.translator, (id) => this.selectOption(id));
    this.timeline = new TimelineTable(byId("timeline"), this.translator);
    this.form = this.#createForm();
  }

  async start() {
    const saved = this.preferences.read();
    await this.translator.load(saved.lang ?? Translator.detectBrowserLanguage());
    this.#translateStaticText();
    this.form.setRaces(await this.api.listRaces(), saved);
    this.form.setPositionText(SAMPLE_POSITION_TEXT);
    await this.map.addBasemap({ kind: "land", landUrl: "mock/atlantic-land-50m.geojson" });
    this.#showResult(await this.api.loadSample());
  }

  async changeLanguage(lang) {
    await this.translator.load(lang);
    this.preferences.update({ lang });
    this.#translateStaticText();
    this.form.retranslate();
    if (this.#result) this.#renderResult();
  }

  selectOption(id) {
    this.#selectedOptionId = id;
    this.#renderResult();
  }

  async compute(request) {
    const result = await this.api.computeRoute(request, (done, total) => this.form.showProgress(done, total));
    this.form.showIdle();
    this.#showResult(result);
  }

  #createForm() {
    return new RouteForm(
      {
        form: byId("route-form"),
        raceSelect: byId("race"),
        boatSelect: byId("boat"),
        positionInput: byId("position"),
        positionFeedback: byId("position-feedback"),
        submitButton: byId("submit"),
      },
      {
        translator: this.translator,
        parser: new PositionParser(),
        onPositionChange: (position) => this.map.showPosition(position),
        onSelectionChange: (selection) => this.preferences.update(selection),
        onSubmit: (request) => this.compute(request),
      },
    );
  }

  #showResult(result) {
    this.#result = result;
    this.#selectedOptionId = result.recommended_option;
    this.#renderResult();
  }

  #renderResult() {
    const result = this.#result;
    const option = result.options.find((o) => o.id === this.#selectedOptionId);
    this.nowPanel.render(result);
    this.optionList.render(result, option.id);
    this.timeline.render(result, option);
    this.map.showResult(result, option.id);
    byId("weather-status").textContent = this.translator.t("weather.status", {
      run: formatUtcHour(result.weather.run),
      next: formatUtcHour(result.weather.next_run_expected),
    });
  }

  #translateStaticText() {
    this.translator.applyTo(document.body);
    this.languagePicker.render(this.translator.lang);
    this.form.showIdle();
    document.title = this.translator.t("app.title");
  }
}

function byId(id) {
  return document.getElementById(id);
}

new App().start();
