// Top of the race card: from-to line with the official distance, and a live status pill
// ("Start in 21 h", "Racing for 2 d 4 h", "Finished").

import { element } from "../dom.js";

const HOUR_MS = 3600 * 1000;

export class RaceHeader {
  constructor(container, translator) {
    this.container = container;
    this.translator = translator;
  }

  render(race, now = new Date()) {
    const t = (key, params) => this.translator.t(key, params);
    const route = element("div", "race-route");
    const line = element("span", "race-route-line");
    line.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3 L8 17 L17 17 Z"/><path d="M5 19 Q12 22 19 19"/></svg>`;
    route.append(element("span", "race-port", race.start_port), line, element("span", "race-port", race.finish_port));

    const meta = element("div", "race-meta");
    const status = this.#status(race, now);
    const pill = element("span", `status-pill ${status.state}`, t(status.key, status.params));
    meta.append(pill, element("span", "race-distance",
      t("race.distance", { distance: race.distance_nm.toLocaleString(this.translator.lang) })));
    this.container.replaceChildren(route, meta);
  }

  #status(race, now) {
    const start = new Date(race.start_time_utc);
    if (now >= new Date(race.close_time_utc)) return { state: "finished", key: "race.status_finished" };
    if (now < start) {
      const hoursLeft = Math.ceil((start - now) / HOUR_MS);
      return hoursLeft < 24
        ? { state: "upcoming", key: "race.status_start_hours", params: { h: hoursLeft } }
        : { state: "upcoming", key: "race.status_start_days", params: { d: Math.floor(hoursLeft / 24), h: hoursLeft % 24 } };
    }
    const elapsed = Math.floor((now - start) / HOUR_MS);
    return { state: "racing", key: "race.status_racing", params: { d: Math.floor(elapsed / 24), h: elapsed % 24 } };
  }
}
