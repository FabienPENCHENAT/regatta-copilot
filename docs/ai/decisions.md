# Decision log

Newest first. Format: decision, why, rejected alternatives. Mark decisions waiting for the user as **PENDING**.

## D27 — Owned boat options drive the routing; sail names follow the game (user feedback, 2026-10-31)
The user owns only the base sails (Jib, Spi) and the foils. Routing with the full pack advised sails they do not
have (light gennaker). Now: `BoatOptions.from_owned("foil")` and `--options` on the CLI; the settings dialog
saves the owned options in the browser (default: foils only) and sends them with each computation; the sail
wardrobe fades and strikes out sails not owned. Comparison on the 2026-10-31 06z run from the start: full pack
2 110 nm left at +120 h, Jib + Spi + foils 2 131 nm, with a more northerly track on day 1.
All five Rhum boats (Class40, IMOCA, Ocean Fifty, Ultim, Vintage Multi) have the same 7 sails, numbered 1–7 in
their polars but spelled differently ("Jib", "jib", "JIB", "LIGHT_JIB"): the parser now names sails from their
number. Options are the same for every boat but their effect differs (foils ×1.084 on the IMOCA, ×1.04 on the
others; hull ×1.003): read from each boat's polar. French names as in the game: Jib, Spi, Trinquette,
Génois léger, Code 0, Spi lourd, Spi léger.

## D26 — Race card redesign and a lean legend (user feedback, 2026-10-31)
The race card was "the least pretty block": the race name is now the title (and the race selector), followed by
a Saint-Malo → Pointe-à-Pitre line with the official distance (3 542 nm, added to the race file), a live status
pill (start countdown / time racing), boats as pills, a position field with a pin and a check mark, and a blue
compute button. The legend keeps only the map symbols plus an always-visible "next data update" line (run every
6 h, usable ~4.5 h later, shown in local time); credits and caveats live on the "How it works" page.

## D25 — Collapsible panels to free the chart (user request, 2026-10-31)
After "Compute my route" the race form collapses to one summary line with an "Edit" button. The whole bottom dock
("set this now" + options) slides down and the whole right column (map tools, legend, route plan) slides right,
each leaving a strip; a click on the strip or on the round toggle brings them back. One reusable class, `PanelCollapser`; the CSS
decides the collapsed look from `data-collapsed`. On phones, panels scroll instead.

## D24 — "Set this now" as instruments; panel toggles removed (user feedback, 2026-10-31)
The rail buttons that hid panels confused the user ("the screen moves but nothing happens"): removed; the rail
keeps theme, settings, "how it works" and language. Map views: 24 h, 48 h, whole race. The "now" panel became
instruments: a compass with the boat on its heading and the wind arrow (TWA visible), the 7-sail wardrobe with
the sail to hoist highlighted, a true-wind bar in the map's wind colours with the Beaufort force, and a speed
dial (0–20 kn). Option cards stack in a column next to it on desktop; the route plan column spans full height.

## D23 — Harmonised look, "How it works" page (user feedback, 2026-10-31)
- Palette built on the "set this now" tiles the user loves: options blue / mint / violet (no red-yellow-green);
  confidence is the intensity of one blue (bars) and of white (glowing map zones), not a traffic light.
- Panels are near-opaque without backdrop blur: the blur over the animated wind particles caused a colour
  shimmer the user noticed on the option cards.
- Font: Geist + Geist Mono (modern); the italic serif and the tagline are gone; sea names in spaced capitals.
- Option cards: one compact row each (small ring, name, one short line; details in the tooltip).
- Tiles: big number + small unit; speed tile in dark ink.
- Logo: faceted mainsail + jib (the minimal jib was not liked). Settings icon: sliders (the cog looked broken).
- `how.html`: a page explaining data sources, refresh times, the isochrone method, options and limits (FR/EN).
- The user now uses the local site (`./run.sh`, http://localhost:8000); the claude.ai preview is no longer updated.

## D22 — Hosting deferred; local site with `./run.sh` (user choice, 2026-10-31)
The user wants "a real site" but chose to stay local until the real engine is wired: `./run.sh` serves the
frontend on port 8000 and prints the LAN address for the phone. It will start FastAPI in step 5. Candidate free
host for later: Hugging Face Spaces (2 vCPU / 16 GB, enough for 31 routes) over Render (512 MB).

## D21 — Theme toggle and settings dialog (user feedback, 2026-10-31)
The settings icon looked like a sun and the user expected a theme switch: the rail now has a real cog for
settings plus a light/dark toggle (`ThemeToggle`, remembered in localStorage; map layers restyle on change).
Settings are a one-column `<dialog>`. The "now" panel follows the selected option, not only the recommended one.
Logo: a single minimal jib (user said "phoque", read as "foc").

## D20 — Map-first glass layout (user reference screenshot, 2026-10-31)
The user sent a dashboard reference (full-bleed muted map, slim icon rail, frosted floating cards, ring metrics,
coloured tiles, glowing hotspots) and asked for that style with the map as the central element. It replaces the
"ocean + light manga" identity and the portolan background of the same day. Target zones are glowing dots
coloured by confidence; panels can be hidden from the rail; map framing uses the free screen area (`map-insets.js`).

## D19 — Backend installed in editable mode, CLI before the API (2026-10-31)
`backend/pyproject.toml` (setuptools, pytest config) + `backend/requirements.txt` (numpy, eccodes, shapely, pytest).
`pip install -e backend` makes `python -m sailrouter` work from any folder; the CLI finds the repo through the
package path, so a non-editable install is not supported. The CLI (`sailrouter/cli/`) is the wiring point until
`api/app_factory.py` exists. FastAPI/uvicorn are not installed yet.

## D18 — Maneuver and speed model V1 (2026-10-31)
Loss per maneuver = `timer × (1 − ratio)` seconds from the polar `winch` block (pro winch by default), timer and
ratio interpolated linearly between `lws` (10 kn) and `hws` (30 kn): Class40 pro tack/gybe 54–90 s, sail change
72–108 s. Tack = TWA sign change with |TWA₁|+|TWA₂| < 180°, gybe otherwise. A tack/gybe with a sail change costs
the larger of the two (assumption: VR timers overlap). No penalty on the first step (current sail and tack
unknown). Foil ramps (TWA and TWS) are multiplied. VR's auto-sail tolerance (1.014) is ignored: the router always
takes the fastest sail. None of this was checked in the game.

## D17 — Mark passing V1 (2026-10-31)
Gates and lines (Fréhel gate, finish) count when a step segment crosses them in the right direction (westward,
northward). `point` marks (Tête à l'Anglais, Basse-Terre buoy, Pointe-à-Pitre buoy) are waypoints reached within
2 nm; the side they are left to is not checked. `island` marks (Les Saintes) are skipped; the land mask keeps the
boat off them. `--next-mark` skips marks already passed (no automatic detection from the position yet).
Once a point passes a mark, points that have not are dropped (costs at most one step).

## D16 — Pruning around the leg anchor, not the next mark (2026-10-31)
The brief said "best point per angular sector around the current target". Seen from Guadeloupe, the bay of
Saint-Brieuc and the Channel lie in the same direction as the open sea, so keeping the point closest to the target
per sector keeps points deep in bays and loses the ones that can round Brittany. Sectors (0.5°) are therefore
taken around the leg anchor (start, or last mark passed) and the farthest point is kept: the true time envelope.
Result: ≈ 700 points per front, 120 h routed in ≈ 4.5 s.

## D15 — Land: 0.005° raster built from the Natural Earth 1:10m chart data (2026-10-31)
The router reuses `frontend/map-data/land.geojson` (≈ 400 m simplification). It is rasterised at 0.005° (≈ 550 m ×
370 m at 48°N) over the weather area: the Fréhel gate (1 nm wide, 470 m from the cape) stays open, Cap Fréhel is
land. Built at each run in ≈ 0.35 s with a numpy scanline fill (bit-packed, 27 MB), so no cache. A 0.08° coarse
raster, dilated by one cell, skips the fine check away from coasts. Outside the area counts as land. Exclusion
zones are checked exactly (planar segment tests), not rasterised. Known limit: a 1:10m coastline misses small
rocks and harbour details; VR uses its own (unknown) land mask.

## D14 — GFS lead times: hourly to f120, 3-hourly after, raw GRIB cache (2026-10-31)
The deterministic GFS 0.25° is hourly up to f120 on NOMADS, then 3-hourly. The router downloads exactly the lead
times covering the routing window (race start tomorrow: run 06z + 30 h to + 150 h = 102 files, 26 MB, ≈ 100 s
the first time at 1 request/s, then 0.2 s from cache). `ForecastStore` keeps the raw GRIB files
(`var/weather/gfs-YYYYMMDDHH/fFFF.grib2`) instead of a decoded `.npz`: decoding takes 0.2 s and partial
downloads resume file by file. A run is assumed complete 5 h after its cycle; the newest run's last lead time is
fetched first and, if NOMADS answers 404 ("data file is not present"), the previous run is used.

## D13 — Race file built from the official sailing instructions (2026-10-31)
`races/route-du-rhum-2026.json` was extracted from the SI PDF (amendments 1 and 2 included): start segments per
class (§9.3), Fréhel gate, marks and sides (annex 3), finish (§10.1), 22 forbidden zones and 2 vigilance zones
(annex 4). Coordinates are `[lat, lon]`. Values not in the SI are flagged `"status": "derived"` (Tête à l'Anglais
position, Les Saintes centre). The "Plaisanciers" zone is a coast-closed line, stored with `"shape": "line"`.

## D12 — Mock-up data uses the real GFS wind and the real Class40 polar (2026-10-31)
The user found the first map unconvincing and the start point wrong. The sample result now starts on the Class40
start line; routes follow hand-made waypoints sailed with the GFS 06z run (2026-10-31) and the VR polar (best
sail, speed). Options and probabilities stay fictional. Generated by a throwaway script, replaced by the real
engine in step 5. All 34 routes were checked against the 1:10m coastline and the forbidden zones.

## D11 — Self-drawn nautical chart instead of OSM tiles (user request, 2026-10-31)
"The map is ugly; I want a nautical chart, with the wind visible." The chart is drawn from vector data:
Natural Earth 1:10m land + bathymetry bands (`scripts/build_basemap.py` → `frontend/map-data/`, 1.5 MB),
graticule, italic sea names, IALA buoy colours, magenta restricted areas, graduated neatline frame.
Works offline and inside published artifacts (which block tile servers). Wind: animated particles
(leaflet-velocity 2.1.4, CSIRO BSD/MIT-style licence) or barbs, with an hour selector. Day = paper chart,
dark mode = ECDIS-like night palette. Rejected: OSM tiles (not nautical, blocked in artifacts), Esri Ocean
basemap (licence terms unclear for free use), OpenSeaMap seamarks (only useful at harbour scale; may be added
as an overlay at high zoom later).

## D10 — Results are route options with probabilities (user request, 2026-10-31)
The user wants several scenarios ("the shortest", "get in place for the weather in 2 days"...), each with a
probability of success, plus a sail/heading advice, at **+4, 8, 12, 16, 24 h** (and +48 h for positioning).
Member routes are clustered into 2–4 options; probability = share of members whose best route is in the option.
Replaces the single consensus route with three cards (5/24/48 h) from the original brief.

## D9 — Frontend without a build step (2026-10-31)
Native ES modules served as static files (by FastAPI later), Leaflet from cdnjs. Simpler than Vite, nothing to
install, the same files are published as the mock-up artifact. Rejected: Vite (no benefit at this size).

## D8 — Mock-up basemap: Natural Earth coastline (2026-10-31)
Published artifacts cannot load OSM tiles (CSP). The mock-up draws `frontend/mock/atlantic-land-50m.geojson`
(Natural Earth 1:50m, public domain, clipped to 0–62°N / 85°W–15°E). The real app uses OSM tiles (`basemap.js`).

## D7 — Advice text is produced client-side from i18n keys (2026-10-31)
The backend returns `{key, params}`; the frontend translates. Keeps all text in `frontend/i18n/*.json`.

## D6 — No hourly weather step (2026-10-31)
GEFS files are 3-hourly from f000 (checked on the 2026-10-31 00z run). The brief asked "hourly up to 3 h";
that resolution does not exist in GEFS. Time interpolation is linear between 3-hourly fields. The routing time
step stays 1 h for the first 24 h, independent of the weather step.

## D5 — Reference repos: inspiration only (2026-10-31)
`keziah744/routeur-rhum`, `thibaro/ultimrouter`, `guime7000/MOwnR`, `Ricou2956/windyvr-lsv-team` have **no licence**
(all rights reserved). `toxcct/VRPolarsChart` is GPL-3.0 (copying would make this project GPL). No code copied.
Facts taken from official race documents (sailing instructions) are re-sourced to those documents.

## D4 — Class40 polar: public community copy of the VR polar (2026-10-31)
The real VR polar `mono/class40-2021` (`_id` 3, VR `_updatedAt` 2024-07-02) is served by
`vro.civis.net` in the raw VR `Meta_GetPolar` format. Used by default, labelled "VR polar, community copy,
not verified in-game". The user's own export from the game, when provided, replaces it (same format).
Rejected: hand-made "approximate" polar (worse than the real one). Rejected: ITYC export (older, 2023-07-03).

## D3 — Weather source: NOAA NOMADS GEFS 0.5°, grib filter (2026-10-31)
Measured costs:
- Open-Meteo Ensemble: **6.2 quota units per point** (2 variables × 31 members), flat up to 10 days; limit
  600 units/min and ~10 000/day. An Atlantic grid at 1° (~4 400 points) would cost ~27 000 units per run:
  impossible. Rejected for the grid.
- NOMADS filter, subregion 5–55°N / 80°W–5°E, UGRD+VGRD 10 m: **56 KB per file at 0.5°**, 223 KB at 0.25°.
  31 members × 41 lead times (5 days, 3-hourly) = 1 271 files ≈ **72 MB per run at 0.5°** (283 MB at 0.25°).
  Downloaded once per run, in the background, throttled.
- Fallback if NOMADS throttles: NOAA AWS bucket `noaa-gefs-pds` (global files, `.idx` byte ranges, no rate limit).
Chosen 0.5°: 4× less data and compute, ensemble spread dominates the resolution error at 24–48 h.

## D2 — Python backend (FastAPI) + vanilla JS frontend (2026-10-31)
As proposed in the brief. numpy for the router, `eccodes` (pip wheel, no system install) for GRIB2.

## D1 — Add the deterministic GFS route as "the game's route" (accepted by the user, 2026-10-31)
VR uses the deterministic GFS 0.25°, not the GEFS members. It is routed as a 32nd member and the option it
belongs to is flagged (`game_route: true`). It does not count in the probabilities (31 GEFS members only).
Cost: ~130 extra small downloads per run.
