// Entry point: creates the components, connects them, and keeps the page state
// (race, result, selected option, selected hour, wind display mode).

import { Translator } from "./i18n/translator.js";
import { LanguagePicker } from "./i18n/language-picker.js";
import { PreferencesStore } from "./storage/preferences-store.js";
import { PositionParser } from "./form/position-parser.js";
import { RouteForm } from "./form/route-form.js";
import { RouteMap } from "./map/route-map.js";
import { MapControls } from "./map/map-controls.js";
import { NowPanel } from "./results/now-panel.js";
import { OptionList } from "./results/option-list.js";
import { TimelineTable } from "./results/timeline-table.js";
import { formatUtcHour } from "./results/display-format.js";
import { MockApi } from "./api/mock-api.js";

const SAMPLE_POSITION_TEXT = `48°43'48"N 001°54'00"W`; // Class40 start line, Saint-Malo

class App {
  #race = null;
  #wind = null;
  #result = null;
  #state = { optionId: null, hour: 0, windMode: "particles", view: "near" };

  constructor() {
    this.api = new MockApi();
    this.preferences = new PreferencesStore();
    this.translator = new Translator();
    this.languagePicker = new LanguagePicker(byId("lang-picker"), (lang) => this.changeLanguage(lang));
    this.map = new RouteMap(byId("map"), this.translator);
    this.mapControls = new MapControls(byId("map-controls"), this.translator, {
      onSelectView: (view) => this.update({ view }),
      onSelectHour: (hour) => this.update({ hour }),
      onSelectMode: (windMode) => this.update({ windMode }),
    });
    this.nowPanel = new NowPanel(byId("now-panel"), this.translator);
    this.optionList = new OptionList(byId("options"), this.translator, (optionId) => this.update({ optionId }));
    this.timeline = new TimelineTable(byId("timeline"), this.translator, (hour) => this.update({ hour }));
    this.form = this.#createForm();
  }

  async start() {
    const saved = this.preferences.read();
    await this.translator.load(saved.lang ?? Translator.detectBrowserLanguage());
    this.#translateStaticText();
    this.form.setRaces(await this.api.listRaces(), saved);
    this.form.setPositionText(SAMPLE_POSITION_TEXT);
    const [race, wind] = await Promise.all([this.api.getRace("route-du-rhum-2026"), this.api.getWindForecast(),
      this.map.loadBasemap({ depthsUrl: "map-data/depths.geojson", landUrl: "map-data/land.geojson" })]);
    this.#race = race;
    this.#wind = wind;
    this.map.showCourse(race, byId("boat").value);
    this.#showResult(await this.api.loadSample());
  }

  async changeLanguage(lang) {
    await this.translator.load(lang);
    this.preferences.update({ lang });
    this.#translateStaticText();
    this.form.retranslate();
    this.map.retranslate();
    if (this.#race) this.map.showCourse(this.#race, byId("boat").value);
    if (this.#result) this.#render({ fitMap: false });
  }

  update(changes) {
    const viewChanged = "view" in changes;
    this.#state = { ...this.#state, ...changes };
    this.#render({ fitMap: viewChanged });
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
        onSelectionChange: (selection) => {
          this.preferences.update(selection);
          if (this.#race) this.map.showCourse(this.#race, selection.boatId);
        },
        onSubmit: (request) => this.compute(request),
      },
    );
  }

  #showResult(result) {
    this.#result = result;
    this.#state = { ...this.#state, optionId: result.recommended_option, hour: 0, view: "near" };
    this.#render({ fitMap: true });
  }

  #render({ fitMap }) {
    const result = this.#result;
    const { optionId, hour, windMode, view } = this.#state;
    const option = result.options.find((o) => o.id === optionId);
    const step = option.steps.find((s) => s.hour === hour);
    this.nowPanel.render(result);
    this.optionList.render(result, option.id);
    this.timeline.render(result, option, hour);
    this.map.showResult(result, option);
    if (fitMap) this.map.fitView(result, view);
    this.map.showBoat(option, hour, (step ?? option.now).heading_deg);
    this.#renderWind(hour, windMode, view);
    byId("weather-status").textContent = this.translator.t("weather.status", {
      run: formatUtcHour(result.weather.run),
      next: formatUtcHour(result.weather.next_run_expected),
    });
  }

  #renderWind(hour, windMode, view) {
    const hours = this.#wind.times.map((time) => time.hour);
    const time = this.#wind.times.find((t) => t.hour === hour) ?? this.#wind.times[0];
    this.map.showWind(time.grid, windMode);
    this.mapControls.render({ view, hours, hour: time.hour, windMode });
    byId("wind-source").textContent = this.translator.t("wind.source", { run: formatUtcHour(this.#wind.run) });
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
