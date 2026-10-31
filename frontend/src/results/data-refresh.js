// When the site's data will next be refreshed: NOAA issues a run every 6 h and it is usable about 4.5 h later.

const RUN_INTERVAL_H = 6;
const PUBLICATION_DELAY_H = 4.5;
const HOUR_MS = 3600 * 1000;

export function nextDataRefresh(runIso, now = new Date()) {
  let next = new Date(new Date(runIso).getTime() + (RUN_INTERVAL_H + PUBLICATION_DELAY_H) * HOUR_MS);
  while (next <= now) next = new Date(next.getTime() + RUN_INTERVAL_H * HOUR_MS);
  return next;
}

// "Next data update around 17:30 (in 2 h 10 min)", in the viewer's local time.
export function describeNextRefresh(translator, runIso, now = new Date()) {
  const next = nextDataRefresh(runIso, now);
  const sameDay = next.toDateString() === now.toDateString();
  const time = next.toLocaleString(translator.lang, sameDay
    ? { hour: "2-digit", minute: "2-digit" }
    : { weekday: "short", hour: "2-digit", minute: "2-digit" });
  const minutes = Math.round((next - now) / 60000);
  const delay = minutes >= 60
    ? translator.t("refresh.hours_minutes", { h: Math.floor(minutes / 60), m: String(minutes % 60).padStart(2, "0") })
    : translator.t("refresh.minutes", { m: minutes });
  return translator.t("refresh.next", { time, delay });
}
