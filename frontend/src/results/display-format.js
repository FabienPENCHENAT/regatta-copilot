// Formats numbers the way sailors read them in the game: DMS coordinates, 3-digit headings, signed TWA.

export function formatCoordinates({ lat, lon }) {
  return `${formatAngle(lat, 2, lat >= 0 ? "N" : "S")} ${formatAngle(lon, 3, lon >= 0 ? "E" : "W")}`;
}

function formatAngle(value, degreeDigits, hemisphere) {
  const totalSeconds = Math.round(Math.abs(value) * 3600);
  const degrees = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${pad(degrees, degreeDigits)}°${pad(minutes, 2)}'${pad(seconds, 2)}"${hemisphere}`;
}

export function formatHeading(degrees) {
  return `${pad(Math.round(((degrees % 360) + 360) % 360), 3)}°`;
}

// Positive TWA = wind on starboard. Returns { angle: "87°", tackKey: "tack.starboard" }.
export function describeTwa(twaDeg) {
  return {
    angle: `${Math.abs(Math.round(twaDeg))}°`,
    tackKey: twaDeg >= 0 ? "tack.starboard" : "tack.port",
  };
}

// Decimal separator follows the language: 5,5 in French, 5.5 in English.
export function formatNumber(value, lang, digits = 1) {
  return value.toLocaleString(lang, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function formatKnots(value, translator) {
  return translator.t("unit.knots", { value: formatNumber(value, translator.lang) });
}

// null while only one forecast is routed (no ensemble yet).
export function confidenceLevel(share) {
  if (share === null || share === undefined) return null;
  if (share >= 0.7) return "high";
  if (share >= 0.4) return "medium";
  return "low";
}

export function formatLocalTime(isoDate, hoursLater, lang) {
  const date = new Date(new Date(isoDate).getTime() + hoursLater * 3600 * 1000);
  return date.toLocaleString(lang, { weekday: "short", hour: "2-digit", minute: "2-digit" });
}

function pad(value, digits) {
  return String(value).padStart(digits, "0");
}
