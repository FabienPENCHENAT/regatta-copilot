// "Set this now" for the recommended option: colour tiles for heading and sail (what you type in the game),
// plain tiles for wind and speed, then the advice sentence.

import { describeTwa, formatHeading, formatKnots } from "./display-format.js";
import { createTermTip } from "./term-tip.js";
import { element } from "../dom.js";

export class NowPanel {
  constructor(container, translator) {
    this.container = container;
    this.translator = translator;
  }

  render(result) {
    const t = (key, params) => this.translator.t(key, params);
    const option = result.options.find((o) => o.id === result.recommended_option);
    const now = option.now;
    const twa = describeTwa(now.twa_deg);

    const head = element("div", "panel-head");
    head.append(element("h2", "panel-title", t("now.title")),
      element("span", "panel-subtitle", t("now.for_option", { option: t(`option.name.${option.id}`) })));
    const tiles = element("div", "tiles");
    tiles.append(
      this.#tile("tile-heading", t("label.heading"), formatHeading(now.heading_deg), "tip.heading"),
      this.#tile("tile-sail", t("label.sail"), t(`sail.${now.sail}`)),
      this.#tile("tile-plain", t("label.tws"), formatKnots(now.tws_kn, this.translator), "tip.tws",
        `${t("label.twa")} ${twa.angle} ${t(twa.tackKey)}`),
      this.#tile("tile-plain", t("label.speed"), formatKnots(now.speed_kn, this.translator)),
    );
    const advice = element("p", "advice", t(result.advice.key, { ...result.advice.params, direction: { key: `direction.${result.advice.params.option}` } }));
    this.container.replaceChildren(head, tiles, advice);
  }

  #tile(className, label, value, tipKey = null, detail = "") {
    const tile = element("div", `tile ${className}`);
    const labelRow = element("span", "tile-label", label);
    if (tipKey) labelRow.append(createTermTip(this.translator, tipKey));
    tile.append(labelRow, element("span", "tile-value", value));
    if (detail) tile.append(element("span", "tile-detail", detail));
    return tile;
  }
}
