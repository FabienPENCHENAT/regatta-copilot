// "Polar and options" page: the boat's polar for the player's options and for the options being tried, at a
// chosen wind speed, the speed gained by angle, and the miles gained on the route. Never changes the settings
// unless the player keeps the tried options.

import { PolarChart } from "./polar-chart.js";
import { OptionToggles } from "./option-toggles.js";
import { RouteImpact } from "./route-impact.js";
import { PositionParser } from "../form/position-parser.js";

const DEFAULT_TWS = 12;
const COMPARED_TWA = [40, 160]; // the angles actually sailed: averages leave out dead upwind and dead downwind

export class PolarPage {
  #twa = [];
  #curves = { current: null, tried: null };
  #tws = DEFAULT_TWS;
  #markerTwa = 90;
  #loads = 0;

  constructor(dom, { api, translator, preferences }) {
    Object.assign(this, { dom, api, translator, preferences });
    const saved = preferences.read();
    this.boat = { raceId: saved.raceId, boatId: saved.boatId };
    this.position = saved.positionText ? new PositionParser().parse(saved.positionText) : null;
    this.chart = new PolarChart(dom.chart, translator);
    this.toggles = new OptionToggles(dom.toggles, { translator, owned: saved.boatOptions, onChange: () => this.#optionsChanged() });
    this.impact = new RouteImpact(dom.impact, { api, translator });
    this.impact.bind(() => this.#impactContext());
    this.#bindControls();
  }

  async start() {
    if (!this.boat.raceId || !this.boat.boatId) {
      const races = await this.api.listRaces();
      const race = races.find((r) => r.id === this.boat.raceId) ?? races[0];
      this.boat = { raceId: race.id, boatId: race.boats.includes(this.boat.boatId) ? this.boat.boatId : race.default_boat };
    }
    this.render();
    await this.#loadCurves();
  }

  render() {
    const t = (key, params) => this.translator.t(key, params);
    this.dom.boat.textContent = t("polar.boat_line", { boat: t(`boat.${this.boat.boatId}`), race: t(`race.${this.boat.raceId}`) });
    this.dom.twsValue.textContent = t("polar.tws_value", { tws: this.#tws });
    this.dom.twaValue.textContent = t("polar.twa_value", { twa: this.#markerTwa });
    this.toggles.render();
    this.impact.render();
    this.#renderCurves();
  }

  #bindControls() {
    this.dom.tws.value = String(this.#tws);
    this.dom.tws.addEventListener("input", () => {
      this.#tws = Number(this.dom.tws.value);
      this.dom.twsValue.textContent = this.translator.t("polar.tws_value", { tws: this.#tws });
      this.#loadCurves();
    });
    this.dom.twa.value = String(this.#markerTwa);
    this.dom.twa.addEventListener("input", () => this.#showAngle(Number(this.dom.twa.value)));
    this.dom.chart.addEventListener("pointermove", (event) => this.#showAngle(this.chart.angleAt(event.clientX, event.clientY)));
    this.dom.reset.addEventListener("click", () => this.toggles.reset());
    this.dom.keep.addEventListener("click", () => this.#keepOptions());
  }

  #showAngle(twa) {
    this.#markerTwa = Math.round(twa / 2) * 2; // curves are sampled every 2°
    this.dom.twa.value = String(this.#markerTwa);
    this.dom.twaValue.textContent = this.translator.t("polar.twa_value", { twa: this.#markerTwa });
    this.#renderCurves();
  }

  #optionsChanged() {
    this.dom.kept.textContent = "";
    this.impact.clear();
    this.impact.render();
    this.#loadCurves();
  }

  // Both curves for the current wind speed; only the answer to the latest request is drawn.
  async #loadCurves() {
    const load = ++this.#loads;
    const [current, tried] = await Promise.all([this.toggles.owned, this.toggles.tried].map((options) =>
      this.api.getPolarCurves(this.boat, [this.#tws], options)));
    if (load !== this.#loads) return;
    this.#twa = current.twa;
    this.#curves = { current: current.curves[0], tried: tried.curves[0] };
    this.#renderCurves();
  }

  #renderCurves() {
    const { current, tried } = this.#curves;
    if (!current) return;
    this.chart.render({ twa: this.#twa, current, changed: tried, markerTwa: this.#markerTwa });
    this.#renderReadout();
    this.#renderSummary();
    this.#renderLegend();
  }

  #renderReadout() {
    const i = this.#twa.indexOf(this.#markerTwa);
    const { current, tried } = this.#curves;
    this.dom.readout.textContent = this.translator.t("polar.readout", {
      twa: this.#markerTwa, before: this.#knots(current.speed[i]), after: this.#knots(tried.speed[i]),
      sail: this.translator.t(`sail.${tried.sail[i]}`), delta: this.#percent(gainPercent(current.speed[i], tried.speed[i])),
    });
  }

  #renderSummary() {
    const t = (key, params) => this.translator.t(key, params);
    if (!this.toggles.changed) {
      this.dom.summary.textContent = t("polar.summary.none");
      return;
    }
    const gains = this.#twa.map((a, i) => ({ twa: a, gain: gainPercent(this.#curves.current.speed[i], this.#curves.tried.speed[i]) }))
      .filter(({ twa }) => twa >= COMPARED_TWA[0] && twa <= COMPARED_TWA[1]);
    const best = gains.reduce((a, b) => (Math.abs(b.gain) > Math.abs(a.gain) ? b : a));
    const mean = gains.reduce((sum, g) => sum + g.gain, 0) / gains.length;
    this.dom.summary.textContent = Math.abs(best.gain) < 0.05
      ? t("polar.summary.same", { tws: this.#tws })
      : t("polar.summary.gain", { best: this.#percent(best.gain), twa: best.twa, mean: this.#percent(mean), tws: this.#tws });
  }

  #renderLegend() {
    const sails = [...new Set(this.#curves.tried.sail)];
    this.dom.legend.replaceChildren(...sails.map((sail) => {
      const item = document.createElement("li");
      const swatch = document.createElement("span");
      swatch.className = "polar-swatch";
      swatch.style.background = `var(--sail-${sail})`;
      item.append(swatch, this.translator.t(`sail.${sail}`));
      return item;
    }));
  }

  #impactContext() {
    const level = this.toggles.owned.pro_winch ? "pro" : "std";
    const sameWinch = this.toggles.owned.pro_winch === this.toggles.tried.pro_winch;
    const saved = this.preferences.read();
    return {
      ...this.boat, position: this.position, current: this.toggles.owned, changed: this.toggles.tried,
      changedAnything: this.toggles.changed, nextMark: saved.nextMark ?? null,
      // Own manoeuvre times only when both sides use the same winch; otherwise the game's values for each.
      maneuvers: sameWinch ? saved.maneuvers?.[`${this.boat.boatId}:${level}`] ?? {} : {},
    };
  }

  #keepOptions() {
    this.preferences.update({ boatOptions: this.toggles.tried });
    this.toggles.adopt();
    this.impact.clear();
    this.dom.kept.textContent = this.translator.t("polar.kept");
    this.render();
  }

  #knots(value) {
    return value.toLocaleString(this.translator.lang, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  }

  #percent(value) {
    return value.toLocaleString(this.translator.lang, { maximumFractionDigits: 1, signDisplay: "exceptZero" });
  }
}

function gainPercent(before, after) {
  return before > 0 ? ((after - before) / before) * 100 : 0;
}
