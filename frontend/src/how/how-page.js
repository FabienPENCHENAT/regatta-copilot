// "How it works" page: lays out the explanation sections. The text itself lives in i18n/*.json.

import { element } from "../dom.js";

const SECTIONS = [
  { key: "how.data", items: ["gfs", "gefs", "polar", "course", "geo"], list: "ul" },
  { key: "how.fresh", paragraphs: ["runs", "cache", "when", "now"] },
  { key: "how.route", paragraphs: ["intro"], items: ["1", "2", "3", "4", "5", "6", "7", "8"], list: "ol" },
  { key: "how.options", paragraphs: ["why", "probability", "confidence", "now"] },
  { key: "how.limits", items: ["advice", "game", "polar", "horizon"], list: "ul" },
  { key: "how.sources", paragraphs: ["list"] },
];

export class HowPage {
  constructor(container, translator) {
    this.container = container;
    this.translator = translator;
  }

  render() {
    this.container.replaceChildren(...SECTIONS.map((section) => this.#section(section)));
  }

  #section({ key, paragraphs = [], items = [], list = "ul" }) {
    const t = (k) => this.translator.t(`${key}.${k}`);
    const block = element("section", "glass panel how-section");
    block.append(element("h2", "panel-title", t("title")));
    paragraphs.forEach((p) => block.append(element("p", "", t(p))));
    if (items.length) {
      const listElement = element(list, "how-list");
      items.forEach((item) => listElement.append(element("li", "", t(item))));
      block.append(listElement);
    }
    return block;
  }
}
