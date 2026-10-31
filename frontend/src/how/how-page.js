// "How it works" page: the text sits in how.html (data-i18n keys); this only builds the weather-run timeline,
// whose hours depend on the reader's time zone.

import { element } from "../dom.js";

const RUN_HOURS_UTC = [0, 6, 12, 18];
const READY_DELAY_MIN = 4 * 60 + 30; // a NOAA run is usable about 4 h 30 after its nominal hour

export class HowPage {
  constructor(timeline, translator) {
    this.timeline = timeline;
    this.translator = translator;
  }

  render() {
    this.timeline.replaceChildren(...RUN_HOURS_UTC.map((hour) => this.#run(hour)));
  }

  #run(hour) {
    const item = element("li", "how-run");
    item.append(
      element("strong", "", this.translator.t("how.fresh.run", { hour: String(hour).padStart(2, "0") })),
      element("span", "", this.translator.t("how.fresh.ready", { time: this.#localReadyTime(hour) })),
    );
    return item;
  }

  #localReadyTime(hour) {
    const ready = new Date(Date.UTC(2026, 0, 1, hour, READY_DELAY_MIN));
    return ready.toLocaleTimeString(this.translator.lang, { hour: "2-digit", minute: "2-digit" });
  }
}
