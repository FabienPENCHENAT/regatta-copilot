// "Set this now": heading, sail and wind for the recommended option, plus the advice sentence.

import { describeTwa, formatHeading, formatKnots } from "./display-format.js";
import { labelWithTip } from "./term-tip.js";
import { element } from "../dom.js";

export class NowPanel {
  constructor(container, translator) {
    this.container = container;
    this.translator = translator;
  }

  render(result) {
    const t = (key, params) => this.translator.t(key, params);
    const option = result.options.find((o) => o.id === result.recommended_option);
    const first = option.now;
    const twa = describeTwa(first.twa_deg);

    const title = element("h2", "now-title", t("now.title"));
    const subtitle = element("p", "now-subtitle", t("now.for_option", { option: t(`option.name.${option.id}`) }));
    const figures = element("dl", "now-figures");
    figures.append(
      figure(labelWithTip(this.translator, "label.heading", "tip.heading"), formatHeading(first.heading_deg), "big"),
      figure(t("label.sail"), t(`sail.${first.sail}`), "big"),
      figure(labelWithTip(this.translator, "label.twa", "tip.twa"), `${twa.angle} ${t(twa.tackKey)}`),
      figure(labelWithTip(this.translator, "label.tws", "tip.tws"), formatKnots(first.tws_kn, this.translator)),
      figure(t("label.speed"), formatKnots(first.speed_kn, this.translator)),
    );
    const advice = element("p", "now-advice", t(result.advice.key, this.#adviceParams(result.advice.params)));
    this.container.replaceChildren(title, subtitle, figures, advice);
  }

  #adviceParams(params) {
    return { ...params, direction: { key: `direction.${params.option}` } };
  }
}

function figure(label, value, size = "") {
  const wrapper = element("div", `now-figure ${size}`.trim());
  const dt = element("dt");
  dt.append(label);
  wrapper.append(dt, element("dd", "", value));
  return wrapper;
}
