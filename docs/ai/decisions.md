# Decision log

Newest first. Format: decision, why, rejected alternatives. Mark decisions waiting for the user as **PENDING**.

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
