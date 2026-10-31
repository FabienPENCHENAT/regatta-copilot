// "Set this now" for the selected option: colour tiles for heading and sail (what you type in the game),
// then wind and speed, each with a big number and a small unit, and the overall advice sentence.

import { describeTwa, formatHeading, formatNumber } from "./display-format.js";
import { createTermTip } from "./term-tip.js";
import { element } from "../dom.js";

export class NowPanel {
  constructor(container, translator) {
    this.container = container;
    this.translator = translator;
  }

  render(result, option) {
    const t = (key, params) => this.translator.t(key, params);
    const now = option.now;
    const twa = describeTwa(now.twa_deg);
    const knots = t("unit.knots_symbol");

    const head = element("div", "panel-head");
    head.append(element("h2", "panel-title", t("now.title")),
      element("span", "panel-subtitle", t("now.for_option", { option: t(`option.name.${option.id}`) })));
    const tiles = element("div", "tiles");
    tiles.append(
      this.#tile("tile-heading", t("label.heading"), formatHeading(now.heading_deg), "", "tip.heading"),
      this.#tile("tile-sail", t("label.sail"), t(`sail.${now.sail}`)),
      this.#tile("tile-plain", t("label.tws"), formatNumber(now.tws_kn, this.translator.lang), knots, "tip.tws",
        `${t("label.twa")} ${twa.angle} ${t(twa.tackKey)}`),
      this.#tile("tile-speed", t("label.speed"), formatNumber(now.speed_kn, this.translator.lang), knots, null,
        t("now.speed_detail")),
    );
    const advice = element("p", "advice", t(result.advice.key,
      { ...result.advice.params, direction: { key: `direction.${result.advice.params.option}` } }));
    this.container.replaceChildren(head, tiles, advice);
  }

  #tile(className, label, value, unit = "", tipKey = null, detail = "") {
    const tile = element("div", `tile ${className}`);
    const labelRow = element("span", "tile-label", label);
    if (tipKey) labelRow.append(createTermTip(this.translator, tipKey));
    const valueRow = element("span", "tile-value", value);
    if (unit) valueRow.append(element("span", "tile-unit", unit));
    tile.append(labelRow, valueRow);
    if (detail) tile.append(element("span", "tile-detail", detail));
    return tile;
  }
}
