// Entry point: creates the components, connects them, and keeps the page state
// (race, result, selected option, selected hour, wind display mode, map view).

import { Translator } from "./i18n/translator.js";
import { LanguagePicker } from "./i18n/language-picker.js";
import { PreferencesStore } from "./storage/preferences-store.js";
import { legAt, planLegs } from "./results/plan-legs.js";
import { PositionParser } from "./form/position-parser.js";
import { RouteForm } from "./form/route-form.js";
import { RaceHeader } from "./form/race-header.js";
import { NextMarkPicker } from "./form/next-mark-picker.js";
import { RouteMap } from "./map/route-map.js";
import { MapControls } from "./map/map-controls.js";
import { WindForecastCache } from "./map/wind-forecast-cache.js";
import { NowPanel } from "./results/now-panel.js";
import { OptionList } from "./results/option-list.js";
import { RoutePlanList } from "./results/route-plan-list.js";
import { describeNextRefresh } from "./results/data-refresh.js";
import { EnsembleStatus } from "./results/ensemble-status.js";
import { SettingsPanel } from "./settings/settings-panel.js";
import { PanelCollapser } from "./layout/panel-collapser.js";
import { ThemeToggle } from "./layout/theme-toggle.js";
import { measureMapInsets } from "./layout/map-insets.js";
import { ApiClient } from "./api/api-client.js";
import { RouteComputation } from "./api/route-computation.js";

const WIND_SETTLE_MS = 200; // time bar: wait for the slider to rest before fetching the wind of that hour
const SETTINGS_SETTLE_MS = 1200; // settings changed in a row (several sails ticked) make a single computation
const DEFAULT_POSITION_TEXT = `48°43'05"N 002°08'38"W`; // the game's start (north end of its line)

class App {
  #race = null;
  #result = null;
  #latestRequest = 0; // only the answer to the latest request is shown
  #settleTimer = null;
  #windTimer = null;
  #state = { optionId: null, hour: 0, windMode: "particles", view: "near" };

  constructor() {
    this.api = new ApiClient();
    this.computation = new RouteComputation(this.api);
    this.wind = new WindForecastCache(this.api);
    this.preferences = new PreferencesStore();
    this.translator = new Translator();
    this.languagePicker = new LanguagePicker(byId("lang-picker"), (lang) => this.changeLanguage(lang));
    this.map = new RouteMap(byId("map"), this.translator, { onSelectHour: (hour) => this.update({ hour }) });
    this.mapControls = new MapControls(byId("map-controls"), this.translator, {
      onSelectView: (view) => this.update({ view }),
      onSelectHour: (hour) => this.update({ hour }),
      onSelectMode: (windMode) => this.update({ windMode }),
    });
    this.nowPanel = new NowPanel(byId("now-panel"), this.translator);
    this.optionList = new OptionList(byId("options"), this.translator, (optionId) => this.update({ optionId }));
    this.routePlan = new RoutePlanList(byId("plan"), this.translator, (hour) => this.update({ hour }));
    this.settings = new SettingsPanel(byId("settings"), byId("settings-open"), {
      api: this.api,
      translator: this.translator,
      preferences: this.preferences,
      onChange: () => this.#recomputeSoon(), // sails and manoeuvre times change the best route
      onPolarChange: () => this.#loadBoat(this.form.boatId).then(() => this.form.submit()),
    });
    this.nextMark = new NextMarkPicker(byId("next-mark"), {
      translator: this.translator, preferences: this.preferences, onChange: () => this.#recomputeSoon(),
    });
    this.formPanel = new PanelCollapser(byId("route-form"), { toggle: byId("form-edit"), translator: this.translator, labelToggle: false });
    this.dockPanel = new PanelCollapser(byId("dock"), { toggle: byId("dock-toggle"), translator: this.translator, expandOnPanelClick: true });
    this.toolsPanel = new PanelCollapser(byId("tools"), { toggle: byId("tools-toggle"), translator: this.translator, expandOnPanelClick: true });
    this.themeToggle = new ThemeToggle(byId("theme-toggle"), {
      translator: this.translator, preferences: this.preferences, onChange: () => this.#redrawForTheme(),
    });
    this.form = this.#createForm();
    this.raceHeader = new RaceHeader(byId("race-header"), this.translator);
    this.ensembleStatus = new EnsembleStatus(byId("ensemble-status"), {
      api: this.api, translator: this.translator, onReady: () => this.form.submit(),
    });
  }

  async start() {
    const saved = this.preferences.read();
    await this.translator.load(saved.lang ?? Translator.detectBrowserLanguage());
    this.#translateStaticText();
    this.#showResultPanels(false);
    this.form.setRaces(await this.api.listRaces(), saved);
    this.form.setPositionText(saved.positionText ?? DEFAULT_POSITION_TEXT);
    const [race] = await Promise.all([
      this.api.getRace(this.form.raceId),
      this.map.loadBasemap({ depthsUrl: "map-data/depths.geojson", landUrl: "map-data/land.geojson" }),
    ]);
    this.#race = race;
    this.raceHeader.render(race);
    this.nextMark.render(race);
    await this.#loadBoat(this.form.boatId);
    this.form.submit();
  }

  async changeLanguage(lang) {
    await this.translator.load(lang);
    this.preferences.update({ lang });
    this.#translateStaticText();
    this.form.retranslate();
    this.map.retranslate();
    this.settings.retranslate();
    this.nextMark.retranslate();
    if (this.#race) {
      this.map.showCourse(this.#race, this.form.boatId);
      this.raceHeader.render(this.#race);
    }
    if (this.#result) this.#render({ fitMap: false });
    this.ensembleStatus.render();
  }

  update(changes) {
    this.#state = { ...this.#state, ...changes };
    this.#render({ fitMap: "view" in changes });
  }

  // Recomputes the shown result once the settings stop changing for a moment.
  #recomputeSoon() {
    if (!this.#result) return;
    clearTimeout(this.#settleTimer);
    this.#settleTimer = setTimeout(() => this.form.submit(), SETTINGS_SETTLE_MS);
  }

  async compute(request) {
    clearTimeout(this.#settleTimer);
    const requestNumber = ++this.#latestRequest;
    this.form.showBusy();
    this.#showComputing(true);
    try {
      const { result, wind } = await this.computation.run({
        ...request, ...this.settings.request, nextMark: this.nextMark.value,
      });
      if (requestNumber !== this.#latestRequest) return; // a newer request replaced this one
      if (result.next_mark) this.nextMark.showDetected(result.next_mark.id);
      this.preferences.update({ positionText: this.form.positionText });
      this.form.showIdle();
      this.#showComputing(false);
      this.formPanel.collapse();
      this.wind.reset(wind);
      this.#showResult(result);
    } catch (error) {
      if (requestNumber !== this.#latestRequest) return;
      this.form.showIdle();
      this.#showComputing(false);
      this.form.showError(this.translator.t("form.compute_error", { reason: error.message }));
    }
  }

  #showComputing(visible) {
    const status = byId("compute-status");
    status.textContent = this.translator.t("compute.running");
    status.hidden = !visible;
  }

  #createForm() {
    return new RouteForm(
      {
        form: byId("route-form"), raceSelect: byId("race"), boatPicker: byId("boat-picker"),
        positionFields: byId("position"), positionFeedback: byId("position-feedback"),
        submitButton: byId("submit"), summary: byId("form-summary-text"),
      },
      {
        translator: this.translator,
        parser: new PositionParser(),
        onPositionChange: (position) => this.map.showPosition(position),
        onSelectionChange: async (selection) => {
          this.preferences.update(selection);
          await this.#loadBoat(selection.boatId);
          if (this.#result) this.form.submit(); // another boat, another speed: recompute
        },
        onSubmit: (request) => this.compute(request),
      },
    );
  }

  // Start line on the map and manoeuvre times of the chosen boat.
  async #loadBoat(boatId) {
    if (this.#race) this.map.showCourse(this.#race, boatId);
    const polar = await this.api.getPolar(this.form.raceId, boatId).catch(() => null);
    this.settings.showPolar(this.form.raceId, boatId, polar);
  }

  #showResult(result) {
    this.#result = result;
    this.#state = { ...this.#state, optionId: result.recommended_option, hour: 0, view: "near" };
    this.#showResultPanels(true);
    this.ensembleStatus.show(result.ensemble);
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
    const leg = legAt(option.legs, hour);
    this.nowPanel.render(result, option, this.settings.ownedSails());
    this.optionList.render(result, option.id);
    this.routePlan.render(result, option, hour);
    this.map.showResult(result, option, hour);
    if (fitMap) this.map.fitView(result, view, measureMapInsets());
    this.map.showBoat(option, Math.min(hour, option.path.length - 1), (leg ?? option.now).heading_deg);
    this.#renderWind(hour, windMode, view, option);
    byId("refresh-text").textContent = describeNextRefresh(this.translator, result.weather.run);
  }

  #redrawForTheme() {
    this.map.refreshTheme();
    if (this.#race) this.map.showCourse(this.#race, this.form.boatId);
    if (this.#result) this.#render({ fitMap: false });
  }

  // Shows the closest loaded wind at once, then the exact hour as soon as it arrives.
  // While the time bar is dragged, only the hour the slider rests on is fetched (WIND_SETTLE_MS).
  #renderWind(hour, windMode, view, option) {
    const windHour = Math.floor(hour); // the map wind is fetched by whole hour
    const shown = this.wind.nearest(windHour);
    this.map.showWind(shown.grid, windMode);
    const marks = planLegs(option).map((leg) => leg.start_hour).filter((h) => h > 0); // the numbered orders
    this.mapControls.render({
      view, hour, windMode,
      timeline: { maxHour: option.path.length - 1, marks, startIso: this.#result.computed_at },
    });
    clearTimeout(this.#windTimer);
    if (shown.exact) return;
    this.#windTimer = setTimeout(() => this.wind.load(windHour).then((loaded) => {
      if (loaded && this.#state.hour === hour) this.map.showWind(this.wind.nearest(windHour).grid, this.#state.windMode);
    }), WIND_SETTLE_MS);
  }

  #translateStaticText() {
    this.translator.applyTo(document.body);
    this.languagePicker.render(this.translator.lang);
    this.themeToggle.render();
    this.mapControls.retranslate();
    [this.formPanel, this.dockPanel, this.toolsPanel].forEach((panel) => panel?.render());
    this.form.showIdle();
    document.title = this.translator.t("app.title");
  }
}

function byId(id) {
  return document.getElementById(id);
}

new App().start();
