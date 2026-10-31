// Entry point: creates the components, connects them, and keeps the page state
// (race, result, selected option, selected hour, wind display mode, map view).

import { Translator } from "./i18n/translator.js";
import { LanguagePicker } from "./i18n/language-picker.js";
import { PreferencesStore } from "./storage/preferences-store.js";
import { PositionParser } from "./form/position-parser.js";
import { RouteForm } from "./form/route-form.js";
import { RaceHeader } from "./form/race-header.js";
import { RouteMap } from "./map/route-map.js";
import { MapControls } from "./map/map-controls.js";
import { NowPanel } from "./results/now-panel.js";
import { OptionList } from "./results/option-list.js";
import { RoutePlanList } from "./results/route-plan-list.js";
import { describeNextRefresh } from "./results/data-refresh.js";
import { SettingsPanel } from "./settings/settings-panel.js";
import { PanelCollapser } from "./layout/panel-collapser.js";
import { ThemeToggle } from "./layout/theme-toggle.js";
import { measureMapInsets } from "./layout/map-insets.js";
import { ApiClient } from "./api/api-client.js";
import { RouteComputation } from "./api/route-computation.js";

const DEFAULT_POSITION_TEXT = `48°43'48"N 001°54'00"W`; // Class40 start line, Saint-Malo

class App {
  #race = null;
  #wind = null;
  #result = null;
  #state = { optionId: null, hour: 0, windMode: "particles", view: "near" };

  constructor() {
    this.api = new ApiClient();
    this.computation = new RouteComputation(this.api);
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
    this.routePlan = new RoutePlanList(byId("plan"), this.translator, (hour) => this.update({ hour }));
    this.settings = new SettingsPanel(byId("settings"), byId("settings-open"), {
      translator: this.translator,
      preferences: this.preferences,
      onOptionsChange: () => this.#result && this.form.submit(), // owned sails change the best route
    });
    this.formPanel = new PanelCollapser(byId("route-form"), { toggle: byId("form-edit"), translator: this.translator, labelToggle: false });
    this.dockPanel = new PanelCollapser(byId("dock"), { toggle: byId("dock-toggle"), translator: this.translator, expandOnPanelClick: true });
    this.toolsPanel = new PanelCollapser(byId("tools"), { toggle: byId("tools-toggle"), translator: this.translator, expandOnPanelClick: true });
    this.themeToggle = new ThemeToggle(byId("theme-toggle"), {
      translator: this.translator, preferences: this.preferences, onChange: () => this.#redrawForTheme(),
    });
    this.form = this.#createForm();
    this.raceHeader = new RaceHeader(byId("race-header"), this.translator);
  }

  async start() {
    const saved = this.preferences.read();
    await this.translator.load(saved.lang ?? Translator.detectBrowserLanguage());
    this.#translateStaticText();
    this.#showResultPanels(false);
    this.form.setRaces(await this.api.listRaces(), saved);
    this.form.setPositionText(saved.positionText ?? DEFAULT_POSITION_TEXT);
    const [race, polar] = await Promise.all([
      this.api.getRace(this.form.raceId),
      this.api.getPolar(this.form.raceId, this.form.boatId).catch(() => null),
      this.map.loadBasemap({ depthsUrl: "map-data/depths.geojson", landUrl: "map-data/land.geojson" }),
    ]);
    this.#race = race;
    this.map.showCourse(race, this.form.boatId);
    this.raceHeader.render(race);
    this.settings.showPolar(polar);
    this.form.submit();
  }

  async changeLanguage(lang) {
    await this.translator.load(lang);
    this.preferences.update({ lang });
    this.#translateStaticText();
    this.form.retranslate();
    this.map.retranslate();
    this.settings.retranslate();
    if (this.#race) {
      this.map.showCourse(this.#race, this.form.boatId);
      this.raceHeader.render(this.#race);
    }
    if (this.#result) this.#render({ fitMap: false });
  }

  update(changes) {
    this.#state = { ...this.#state, ...changes };
    this.#render({ fitMap: "view" in changes });
  }

  async compute(request) {
    this.form.showBusy();
    try {
      const { result, wind } = await this.computation.run({ ...request, options: this.settings.options });
      this.preferences.update({ positionText: this.form.positionText });
      this.form.showIdle();
      this.formPanel.collapse();
      this.#wind = wind;
      this.#showResult(result);
    } catch (error) {
      this.form.showIdle();
      this.form.showError(this.translator.t("form.compute_error", { reason: error.message }));
    }
  }

  #createForm() {
    return new RouteForm(
      {
        form: byId("route-form"), raceSelect: byId("race"), boatPicker: byId("boat-picker"),
        positionInput: byId("position"), positionFeedback: byId("position-feedback"),
        submitButton: byId("submit"), summary: byId("form-summary-text"),
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
    this.#showResultPanels(true);
    this.#render({ fitMap: true });
  }

  #showResultPanels(visible) {
    byId("dock").hidden = !visible;
    byId("plan").hidden = !visible;
  }

  #render({ fitMap }) {
    const result = this.#result;
    const { optionId, hour, windMode, view } = this.#state;
    const option = result.options.find((o) => o.id === optionId);
    const step = option.steps.find((s) => s.hour === hour);
    this.nowPanel.render(result, option, this.settings.ownedSails());
    this.optionList.render(result, option.id);
    this.routePlan.render(result, option, hour);
    this.map.showResult(result, option);
    if (fitMap) this.map.fitView(result, view, measureMapInsets());
    this.map.showBoat(option, hour, (step ?? option.now).heading_deg);
    this.#renderWind(hour, windMode, view);
    byId("refresh-text").textContent = describeNextRefresh(this.translator, result.weather.run);
  }

  #redrawForTheme() {
    this.map.refreshTheme();
    if (this.#race) this.map.showCourse(this.#race, this.form.boatId);
    if (this.#result) this.#render({ fitMap: false });
  }

  #renderWind(hour, windMode, view) {
    const hours = this.#wind.times.map((time) => time.hour);
    const time = this.#wind.times.find((t) => t.hour === hour) ?? this.#wind.times[0];
    this.map.showWind(time.grid, windMode);
    this.mapControls.render({ view, hours, hour: time.hour, windMode });
  }

  #translateStaticText() {
    this.translator.applyTo(document.body);
    this.languagePicker.render(this.translator.lang);
    this.themeToggle.render();
    [this.formPanel, this.dockPanel, this.toolsPanel].forEach((panel) => panel?.render());
    this.form.showIdle();
    document.title = this.translator.t("app.title");
  }
}

function byId(id) {
  return document.getElementById(id);
}

new App().start();
