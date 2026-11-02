# Architecture

Status: backend complete for steps 3–4 (GFS + 31 GEFS members, options, API, CLI). Classes are created as the steps progress. Keep this page in sync with the code:
when a class is added, renamed or split, update the table.

## Repository layout

```
routeur-voile/
├── backend/sailrouter/     Python package (FastAPI + routing engine)
├── backend/tests/          pytest, mirrors the package layout
├── frontend/               vanilla JS ES modules + Leaflet, no build step
│   ├── i18n/               fr.json, en.json (all UI text)
│   └── mock/               sample result + coastline used by the mock-up
├── races/                  one JSON file per race (generic format, no code change to add a race)
├── data/polars/            VR polar JSON files (+ sources/ with provenance)
├── frontend/map-data/      land + depth bands for the chart (built by scripts/build_basemap.py)
├── scripts/                dev tools (data builders), not imported by the app
├── var/                    runtime cache, git-ignored (weather runs, computed routes)
└── docs/ai/  docs/founder/
```

## Layers

```
api · cli  HTTP / command line only: request parsing, response JSON, wiring
 │
service    runs a request: GFS route, 31 GEFS member routes (process pool), background GEFS download
 │
ensemble   31 member routes → options, probabilities, confidence, advice
 │
routing    isochrone engine for ONE wind field
 │
weather · polar · geography      independent of each other
 │
domain     value objects: GeoPoint, Race, Mark, ExclusionZone, parsing of user input
```

Dependencies only point downwards. `weather`, `polar` and `geography` never import each other; `routing`
receives them as constructor arguments.

## Packages and classes

Backend status: every package below exists. `service` sits between `api`/`cli` and the engine (it wires
objects and runs the process pool); `ensemble` only depends on `routing` and `domain`.

Commands (from the repo root):
```
/opt/homebrew/bin/python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt -e backend
.venv/bin/python -m pytest backend          # tests, no network
.venv/bin/python -m sailrouter route --position "48°43'48\"N 001°54'00\"W" --hours 120
.venv/bin/python -m sailrouter ensemble-download   # GEFS run for the race window (≈ 15 min the first time)
```

### `domain` — pure value objects, no I/O
| Class | Responsibility |
|---|---|
| `GeoPoint` | Latitude/longitude pair, longitude normalised to [-180, 180). |
| `GreatCircle` | Distance, initial bearing, destination point and signed cross-track distance on the sphere (vectorised, nm). |
| `SegmentIntersector` | Planar segment–segment intersection in (lon, lat) and where a segment meets a line, vectorised (gates, lines, zones). |
| `PositionParser` | Turns user text (`46°12'30"N 012°34'10"W`, `46.21, -12.57`, ...) into a `GeoPoint`. Twin of `frontend/src/form/position-parser.js`. |
| `Mark`, `ExclusionZone`, `RaceBoat`, `Race` | Course definition: ordered marks (gate/line/point; a mark left to one side is a directed gate from the physical mark, `position` = the mark, `target` = where the router aims), finish line, forbidden zones (polygon or line), boats with polar and start line. |

### `course` — loading races
| Class | Responsibility |
|---|---|
| `RaceCatalog` | Lists and loads `races/*.json` into `Race` objects; raises `RaceFileError` on a bad file. |

### `weather` — everything GFS/GEFS
| Class | Responsibility |
|---|---|
| `ModelRun` | One run: model (`gfs`, later `gefs`) + cycle time; `key` names the cache folder. |
| `GfsRunClock` | Which run (00/06/12/18 UTC) should be complete (cycle + 5 h); previous run; when the next is expected. |
| `LeadTimePlan` | Which lead times exist (GFS: hourly to f120, 3-hourly to f384; GEFS: 3-hourly) and which cover a window. |
| `WeatherArea` | Download box (0–60°N, 80°W–10°E). |
| `GfsQueryBuilder` | NOMADS grib-filter query (script + params) for one GFS 0.25° lead time, 10 m U/V only. |
| `NomadsClient` | Downloads one grib-filter file over HTTP/1.1, ≤ 1 request/s (GEFS: 2/s), retries with backoff; 404/HTML → `DataNotAvailable`. |
| `GfsRunDownloader` | Puts the missing lead times of a run into the store; fetches the last one first as a completeness probe. |
| `ForecastStore` | On-disk cache of raw GRIB files, `var/weather/<run key>/fFFF.grib2` (GEFS: `fFFF-<member>.grib2`), written atomically; lists missing files. |
| `GribDecoder` | GRIB2 file → `WindGrid` (ecCodes). |
| `WindGrid` | U/V (m/s) on a regular lat/lon grid at one valid time. |
| `WindField` | Wind of ONE forecast: bilinear in space, linear in time on U/V → TWS (kn), TWD (deg). Vectorised. |
| `GfsWindSource` | The `WindField` of the latest complete GFS run covering a window (falls back to older runs); `cached_run` = newest run already on disk, `download_latest` = download only, `prefer_cached` = no download when a run is on disk. |
| `GefsQueryBuilder` | NOMADS grib-filter query for one GEFS 0.5° member (`c00`, `p01`..`p30`, `GEFS_MEMBERS`) and lead time. |
| `GefsRunDownloader` | Puts every member × lead time of a run in the store; last lead of every member first (completeness probe); progress counts cached files. |
| `GefsRunCatalog` | Candidate GEFS runs (latest due, then 2 older), lead times covering a window (3-hourly to f240), files on disk, newest complete run. |
| `GefsMemberLoader` | Cached GRIB files of one member → its `WindField` (no download). |
| `RunDownloadLock` | `var/weather/<run>.downloading` file (pid, touched per file, stale after 120 s): one download per run across processes. |

### `polar` — boat performance
| Class | Responsibility |
|---|---|
| `VrPolarParser` | Raw VR `Meta_GetPolar` JSON → `VrPolar`. |
| `PlayerPolarReader` | Finds the VR polar in the JSON the player pasted (raw or wrapped at any depth) and checks it (7 sails, tables, `winch`); `InvalidPolarError`. |
| `VrPolar` | Everything a VR polar file holds: `BoatPolar`, `FoilBonus`, hull ratio, `WinchTimings`. |
| `BoatPolar` | Speed tables per sail; bilinear lookup (TWS, \|TWA\|) for all sails at once. |
| `FoilBonus` | Foil speed factor (×1.04 in TWA 80–160 / TWS 16–35, linear merge ramps, ramps multiplied). |
| `WinchTimings`, `ManeuverTiming` | VR `winch` block: timer and speed ratio per maneuver, std/pro, light/heavy wind. |
| `BoatOptions` | Which options the player owns (light/heavy/reach sail packs, foils, hull, pro winch). All on by default. |
| `SpeedModel` | Polar × options → best allowed sail and boat speed for many (TWS, TWA) at once. |
| `ManeuverPenalty` | Seconds lost on tack, gybe, sail change between two states: `timer × (1 − ratio)`, 10–30 kn interpolation, overridable. |

### `geography` — where the boat may not go
| Class | Responsibility |
|---|---|
| `CoastlineLoader` | Reads `frontend/map-data/land.geojson` into valid (`make_valid`), oriented polygons. |
| `RasterGrid` | Regular lat/lon raster geometry: point → cell. |
| `PolygonRasterizer` | Polygons → bit-packed raster (scanline, non-zero winding, pure numpy, ≈ 0.35 s at 0.005°). |
| `LandMask` | "Is this point on land?" on the packed raster (outside = land) + coarse dilated "may be near land" raster. |
| `ZoneCrossingDetector` | Whether segments enter an exclusion zone (polygon: end inside or border crossed from outside; line: touched). |
| `ObstacleChecker` | Whether segments cross land or a zone: coarse sampling first, fine sampling near coasts only. |

### `routing` — one wind field, one route
| Class | Responsibility |
|---|---|
| `TimeSchedule` | Isochrone times: 1 h steps until T+24 h, 3 h beyond, last step cut at the horizon. |
| `HeadingFan` | Candidate headings (every 5°) from each front point. |
| `Isochrone` | One front: positions, parent indices, and the arriving segment's heading, TWA, TWS, sail, speed, leg. |
| `CourseLeg` | One leg: anchor (start / previous mark), target, gate line + crossing direction or waypoint radius. |
| `MarkProgress` | Legs of the race from a position; detects passing (gate/line crossed in its direction, so rounding marks on the right side; waypoint within 2 nm); finishing segments end on the finish line; distance to go; `legs_along` gives the leg index along a given track. |
| `IsochronePruner` | Keeps the most advanced leg, then the farthest point from the leg anchor per 0.5° sector. |
| `IsochroneRouter` | Runs the steps: wind → best sail/speed → maneuver penalty → destination → drop obstacles → marks → prune. |
| `NextMarkFinder` | First mark still ahead of a position (gates/lines crossed by > 2 nm are skipped; rounding marks, with `leave_to`, never are). |
| `RouteLegSplitter` | Cuts a route into legs with the same orders (heading within 10°, sail, tack) for the route plan. |
| `RouteTracer` | Picks the best final point (marks passed, then distance to go) and walks parents back → `Route`. |
| `Route`, `RoutePoint` | Ordered points (time, position, and heading/TWA/TWS/sail/speed of the leg starting there); `position_at(hours)` interpolates. |

### `cli` — command line
| Module | Responsibility |
|---|---|
| `main.py` | `python -m sailrouter route ...` and `ensemble-download`: argument parsing, exit codes. |
| `ensemble_download_command.py` (`EnsembleDownloadCommand`) | Downloads the latest complete GEFS run for a race window in the foreground, with progress. |
| `route_summary_printer.py`, `position_formatter.py` | Text summary at +4/8/12/16/24/48 h in the game's position format. |
| `route_file_writer.py` | `var/routes/<name>.json` (plan + every point + path) and `<name>.geojson` (LineString + horizon points). |

### `ensemble` — route options and their probabilities
The user gets **1 to 4 route options** (e.g. "direct = shortest", "west = get in place for the weather in
2 days"), each with its **probability** (share of the GEFS members whose route goes that way) and a **route
plan**. Pure computation on `Route` objects (decisions D30–D33).
| Class | Responsibility |
|---|---|
| `RouteDistanceMatrix` | Pairwise gap between routes: max(gap at +48 h, 2 × gap at +24 h), nm. |
| `RouteOptionClusterer` | Average-linkage groups (≤ 70 nm), lone members merged into the nearest group, at most 4 groups, largest first. |
| `MedoidPicker` | The member route that represents a group (smallest total distance to the others). |
| `OptionLabeler` | Option id from its side of the fixed line boat → next mark (+48 h gap + 2 × +24 h gap): nearest = `direct` (≤ 150, about 50 nm on average), then on each side the compass name of that side (`north`/`south` on a westward course, `west`/`east` on a southward one), nearest plain, then `_wide`, `_far`; kind `shortest` (closest to the great circle to the next mark) / `positioning`; one option = `consensus`. |
| `ConfidenceGrader` | Step confidence: share of the option's members within the zone radius (3 + 0.9 × hour nm) of the representative. |
| `EtaGapEstimator` | Arrival gap vs the best option: hours sailed + distance to go ÷ the route's mean speed. |
| `AdviceWriter` | Advice as **i18n key + parameters** (never text): `advice.consensus` or `advice.head_direction`. |
| `EnsembleSynthesizer` | Runs the above: member routes + game route → `EnsembleSynthesis` (`RouteOption`s, member → option, advice); flags the option holding the GFS route. |
| `RouteOption`, `EnsembleSynthesis` | Value objects of the result. |

### `service` — application layer shared by the CLI and the API
| Class | Responsibility |
|---|---|
| `RoutePlanner` | Routes one boat on the deterministic GFS (the game's weather) → `RouteReport` (with the next mark used and whether it was automatic); also provides the GFS wind for the map. `prefer_cached` (web): newest run on disk. |
| `RouterBuilder` | Boat models (polar, owned sails, manoeuvre overrides), land + zones obstacles, `IsochroneRouter` for a wind field. |
| `EnsembleRoutePlanner` | Routes the 31 members in a spawned `ProcessPoolExecutor` (cpu − 1 workers) while the GFS route runs in-process, then `EnsembleSynthesizer`, then sails every option's track (and the player's current route, if sent) in every member's wind → `EnsembleReport`. |
| `member_routing_worker` (module) | `MemberRoutingSpec`; per-process `initialize` (race, polar, land raster once) and `route_member` (decode one member, route it). |
| `EnsembleDownloadJob` | One GEFS download at a time in a background thread: `ensure(window)` returns the newest run on disk and starts a newer one; `status()`; `download()` for the CLI; failed runs retried after 10 min. |
| `EnsembleStatus` | `ready` / `downloading` / `unavailable`, run, done/total files, member count. |
| `build_ensemble_job` (`ensemble_job_factory.py`) | Wires the job (NOMADS client at ≤ 2 requests/s). |
| `RouteReport`, `EnsembleReport`, `ProjectPaths` | Results of one run; where data and caches live. |
| `WeatherRefresher` | Background thread, every 10 min: latest GFS run for the route window + 12 h on disk, GEFS job `ensure`, then a pre-computation callback (`weather_changed`). |
| `build_gfs_source` (`gfs_source_factory.py`) | Wires `GfsWindSource` on the project cache. |
| `PlayerPolarStore` | The player's imported polars, `var/polars/<race>-<boat>.vr.json` (safe ids, atomic write, import time = mtime). |
| `BoatPolarLocator` | The polar file a boat sails with (player's, else community), its source and fingerprint for the cache key. |

### `api` — FastAPI
| Module | Responsibility |
|---|---|
| `app_factory.py` | Builds the app: routers under `/api`, frontend files at `/`, one shared `EnsembleDownloadJob`, the `WeatherRefresher` started/stopped with the app (lifespan; `refresh_in_background=False` in tests). |
| `routes_races.py` | Race list, race file. |
| `routes_polars.py` | `GET`/`POST`/`DELETE /api/races/{race}/boats/{boat}/polar`: polar in use (+ `_source`, `_imported_at`), player import, back to community. |
| `routes_routing.py` | `POST /api/route` (through `CachedRouteComputer`, remembers the request), `GET /api/ensemble/status`, `GET /api/wind`. |
| `cached_route_computer.py` (`CachedRouteComputer`) | One route request → stored result or fresh computation (ensemble when the GEFS run is on disk, else GFS only, on the newest GFS run on disk), stored with its key; shared by the endpoint and the refresher. |
| `last_route_request_store.py` (`LastRouteRequestStore`) | Last request received, in memory and in `var/last_request.json`. |
| `last_route_precomputer.py` (`LastRoutePrecomputer`) | Refresher callbacks: route window of the last request's race; recompute the last request when the weather changed (or while it is < 6 h old). |
| `schemas.py` | Request models; converts settings to `BoatOptions`. |
| `route_json_writer.py` (`RouteJsonWriter`) | One `Route` → `now`, `steps`, `legs`, hourly `path`, full track. |
| `route_result_cache.py` | Stored results keyed by inputs + weather run ids (instant reopening until the next run). |
| `route_result_builder.py` | `RouteReport` → GFS-only result (one `gfs` option, nulls). |
| `ensemble_result_builder.py` | `EnsembleReport` → result with options, probabilities, confidence, `members`. |
| `ensemble_status_json.py` | `EnsembleStatus` → the `ensemble` JSON object. |
| `wind_grid_exporter.py` | `WindField` → leaflet-velocity grids for the map. |

### `frontend` — no build step, native ES modules
| Module | Responsibility |
|---|---|
| `src/main.js` (`App`) | Creates and connects the components; holds the current result and selected option. |
| `i18n/translator.js`, `i18n/language-picker.js` | Loads `i18n/<lang>.json`, translates keys; FR/EN toggle. |
| `storage/preferences-store.js` | Last race, boat, language in localStorage. |
| `form/position-parser.js`, `form/route-form.js` | Parses pasted positions; race/boat/position inputs, submit, one-line summary when collapsed. |
| `form/next-mark-picker.js` | "Next mark": automatic (server-detected) or picked by the player; shows the mark the automatic choice used. |
| `form/race-header.js`, `form/boat-picker.js` | From–to line with distance and live race status; boat class pills. |
| `results/data-refresh.js` | Time of the next data update (run every 6 h, usable ~4.5 h later). |
| `map/route-map.js` | Builds the Leaflet chart and its layers; the only map API the app uses. |
| `map/chart-basemap.js` | Nautical-chart background from `map-data/` (depth bands, land, coastline). No tile server. |
| `map/graticule-layer.js`, `map/sea-labels.js` | Degree grid with edge labels; italic sea names (i18n). |
| `map/course-layer.js` | Race course: start line of the chosen boat, gates, marks (IALA colours), finish, forbidden and vigilance zones. |
| `map/route-layer.js` | Computed track, member routes, selected option with numbered leg markers (same numbers as the plan), boat at the selected hour. |
| `map/wind-forecast-cache.js` | Map wind already loaded by hour; fetches any other hour on demand (`/api/wind?hours=11`). |
| `map/wind-grid.js` | Bilinear wind lookup on a leaflet-velocity grid. |
| `map/wind-particles-layer.js`, `map/wind-barbs-layer.js` | Wind as animated particles (leaflet-velocity) or as meteorological barbs (canvas). |
| `map/map-controls.js`, `map/map-style.js` | View (48 h / whole race), hour chips, particles/barbs toggle, knots legend; pane stack and theme colours. |
| `how.html`, `src/how-main.js`, `how/how-page.js` | "How it works" page: data, refresh times, method, options, limits; text in i18n. |
| `layout/theme-toggle.js` | Light/dark switch; follows the system until the user picks, then remembers it. |
| `settings/settings-panel.js`, `settings/boat-options-form.js`, `settings/maneuver-times.js` | Settings dialog: owned sails one by one, editable manoeuvre times pre-filled from the VR polar (saved per boat); any change recomputes. |
| `settings/polar-import.js` | Which polar is used (community or the player's import), import a JSON copied from the game, go back. |
| `layout/panel-collapser.js` | Collapses a floating panel out of the chart's way (form → summary line after computing, "now" panel → slides down, right column → slides right leaving a strip); click brings it back. |
| `results/now-panel.js` | "Set this now" as boat instruments, built from `results/instruments/`: compass dial (heading + wind direction), sail wardrobe, true-wind gauge with Beaufort force, speed dial, side by side under a one-line title naming the option. |
| `results/option-list.js` | Options as a compact table, one selectable row each (probability ring, short name, badges) and the outlook in aligned columns (+48 h, +5 d): green ▲ / red ▼ nm vs the recommended option, which shows its distances to go. The "your current route" row heads it for the eye only, with the menu to pick which previous option it is. |
| `results/route-history.js` | Remembers in the browser the options of the latest computation and of the one from the previous position. |
| `results/followed-route-finder.js` | Recognises the route followed since then: the previous option passing within 30 nm of the new position (the clicked one wins a near tie, the one picked in the menu always wins), the rest of it, and every option with its distance for the menu. |
| `results/option-places.js` | Place in the list (north to south, west to east, direct in between) and colour slot (`--route-1..5`) of an option, from its id alone. |
| `results/plan-legs.js` | The legs shown in both the plan and the map (next 48 h), and the leg at a given hour. |
| `results/route-plan-list.js` | Route plan as orders: one row per leg (start, heading, sail, expected speed in kn and km/h, wind, duration) over 48 h; a leg selects its hour on the map. |
| `results/display-format.js`, `results/term-tip.js`, `dom.js` | Formatting (DMS, headings, decimals per language), jargon tooltips, DOM helper. |
| `api/api-client.js`, `api/route-computation.js` | Calls the backend; one computation = route then map wind. |

The response shape is documented in [api-contract.md](api-contract.md).

## Main data flow

```
user: race + boat + position + owned sails + manoeuvre times
  → POST /api/route → CachedRouteComputer → RaceCatalog → window = [max(race start, now), +120 h]
  → stored result for (inputs, next mark, polar, GFS run on disk, GEFS run)? → answer at once
  → EnsembleDownloadJob.ensure(window): GEFS run on disk? (else download in background, answer with GFS only)
  → EnsembleRoutePlanner: 31 × (GefsMemberLoader → IsochroneRouter → RouteTracer) in worker processes
                          + RoutePlanner on the deterministic GFS (the game's route) in-process
  → EnsembleSynthesizer: RouteDistanceMatrix → RouteOptionClusterer → MedoidPicker → OptionLabeler
                         → probabilities, ConfidenceGrader, EtaGapEstimator, AdviceWriter
  → EnsembleResultBuilder → JSON → frontend (text translated client-side)
```

Background (`WeatherRefresher`, every 10 min while the app runs):
```
window of the last request's race → GfsWindSource.download_latest(window + 12 h) → EnsembleDownloadJob.ensure
  → runs changed (or last request < 6 h old) → CachedRouteComputer.result(last request) → var/results/
```
