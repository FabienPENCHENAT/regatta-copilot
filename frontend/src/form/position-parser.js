// Parses a position typed or pasted by the user. Accepted forms:
//   47°30'00"N 006°45'00"W   47°30.5'N 6°45.2'W   47.5N 6.75W   47.5, -6.75   47,5 ; -6,75
// "O" (ouest) is accepted for west. Returns { lat, lon } in decimal degrees, or null.

const NUMBER = String.raw`(\d+(?:[.,]\d+)?)`;
const HEMISPHERE_PART = new RegExp(
  String.raw`${NUMBER}\s*°?\s*(?:${NUMBER}\s*['′’]\s*)?(?:${NUMBER}\s*(?:["″”]|''))?\s*([NSEWO])`,
  "gi",
);
const SIGNED_DOT_PAIR = /^\s*(-?\d+(?:\.\d+)?)\s*[,;\s]\s*(-?\d+(?:\.\d+)?)\s*$/;
const SIGNED_COMMA_PAIR = /^\s*(-?\d+(?:,\d+)?)\s*[;\s]\s*(-?\d+(?:,\d+)?)\s*$/;

export class PositionParser {
  parse(text) {
    if (!text || !text.trim()) return null;
    const position = this.#parseHemispheres(text) ?? this.#parseSignedPair(text);
    return position && this.#isValid(position) ? position : null;
  }

  #parseHemispheres(text) {
    const parts = [...text.matchAll(HEMISPHERE_PART)];
    if (parts.length !== 2) return null;
    const position = {};
    for (const [, deg, min, sec, letter] of parts) {
      const value = toNumber(deg) + toNumber(min) / 60 + toNumber(sec) / 3600;
      const hemisphere = letter.toUpperCase();
      if (hemisphere === "N" || hemisphere === "S") position.lat = hemisphere === "S" ? -value : value;
      else position.lon = hemisphere === "E" ? value : -value;
    }
    return "lat" in position && "lon" in position ? position : null;
  }

  #parseSignedPair(text) {
    const match = text.match(SIGNED_DOT_PAIR) ?? text.match(SIGNED_COMMA_PAIR);
    return match ? { lat: toNumber(match[1]), lon: toNumber(match[2]) } : null;
  }

  #isValid({ lat, lon }) {
    return Number.isFinite(lat) && Number.isFinite(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180;
  }
}

function toNumber(text) {
  return text ? Number(text.replace(",", ".")) : 0;
}
