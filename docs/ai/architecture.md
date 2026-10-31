# Architecture

Status: backend core built in step 3 (one GFS member, CLI); `ensemble` and `api` planned. Classes are created as the steps progress. Keep this page in sync with the code:
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
api        HTTP only: request parsing, response schemas, wiring
 │
ensemble   31 member routes → zones, confidence, consensus heading/sail, advice
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

Backend status: `domain`, `course`, `weather` (deterministic GFS), `polar`, `geography`, `routing` and the CLI
exist (step 3). `ensemble`, `api` and the GEFS members are still planned (steps 4–5).

Commands (from the repo root):
```
/opt/homebrew/bin/python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt -e backend
.venv/bin/python -m pytest backend          # tests, no network
.venv/bin/python -m sailrouter route --position "48°43'48\"N 001°54'00\"W" --hours 120
```

### `domain` — pure value objects, no I/O
| Class | Responsibility |
|---|---|
| `GeoPoint` | Latitude/longitude pair, longitude normalised to [-180, 180). |
| `GreatCircle` | Distance, initial bearing and destination point on the sphere (vectorised, nm). |
| `SegmentIntersector` | Planar segment–segment intersection in (lon, lat), vectorised (gates, lines, zones). |
| `PositionParser` | Turns user text (`46°12'30"N 012°34'10"W`, `46.21, -12.57`, ...) into a `GeoPoint`. Twin of `frontend/src/form/position-parser.js`. |
| `Mark`, `ExclusionZone`, `RaceBoat`, `Race` | Course definition: ordered marks (gate/line/point/island), finish line, forbidden zones (polygon or line), boats with polar and start line. |

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
| `NomadsClient` | Downloads one grib-filter file over HTTP/1.1, ≤ 1 request/s, retries with backoff; 404/HTML → `DataNotAvailable`. |
| `GfsRunDownloader` | Puts the missing lead times of a run into the store; fetches the last one first as a completeness probe. |
| `ForecastStore` | On-disk cache of raw GRIB files, `var/weather/<run key>/fFFF.grib2`, written atomically. |
| `GribDecoder` | GRIB2 file → `WindGrid` (ecCodes). |
| `WindGrid` | U/V (m/s) on a regular lat/lon grid at one valid time. |
| `WindField` | Wind of ONE forecast: bilinear in space, linear in time on U/V → TWS (kn), TWD (deg). Vectorised. |
| `GfsWindSource` | The `WindField` of the latest complete GFS run covering a window (falls back to older runs). |
| `GefsWindSource`, `EnsembleForecast` | Planned (step 4): one `WindField` per GEFS member, same `WindField` class, `GefsQueryBuilder` with a member number. |

### `polar` — boat performance
| Class | Responsibility |
|---|---|
| `VrPolarParser` | Raw VR `Meta_GetPolar` JSON → `VrPolar`. |
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
| `MarkProgress` | Legs of the race from a position; detects passing (gate crossed westward, waypoint within 2 nm); distance to go. |
| `IsochronePruner` | Keeps the most advanced leg, then the farthest point from the leg anchor per 0.5° sector. |
| `IsochroneRouter` | Runs the steps: wind → best sail/speed → maneuver penalty → destination → drop obstacles → marks → prune. |
| `RouteLegSplitter` | Cuts a route into legs with the same orders (heading within 10°, sail, tack) for the route plan. |
| `RouteTracer` | Picks the best final point (marks passed, then distance to go) and walks parents back → `Route`. |
| `Route`, `RoutePoint` | Ordered points (time, position, and heading/TWA/TWS/sail/speed of the leg starting there). |

### `cli` — command line (wiring for step 3, until `api` exists)
| Module | Responsibility |
|---|---|
| `main.py` | `python -m sailrouter route ...`: argument parsing, exit codes. |
| `route_command.py` (`RouteCommand`) | Builds every object (the only place that knows all layers) and runs one route → `RouteReport`. |
| `route_report.py`, `project_paths.py` | Result of one run; where races, land, polars and `var/` live. |
| `route_summary_printer.py`, `position_formatter.py` | Text summary at +4/8/12/16/24/48 h in the game's position format. |
| `route_file_writer.py` | `var/routes/<name>.json` (plan + every point + path) and `<name>.geojson` (LineString + horizon points). |

### `ensemble` — route options and their probabilities
The user gets **2 to 4 route options** (e.g. "direct = shortest", "west = get in place for the weather in
2 days"), each with its **probability of being the best** and a **route plan at +4/8/12/16/24/48 h**.
| Class | Responsibility |
|---|---|
| `EnsembleRouter` | Runs `IsochroneRouter` for each of the 31 GEFS members + the deterministic GFS (process pool), reports progress. |
| `RouteOptionClusterer` | Groups the member routes into options by where they are at +24 h and +48 h. |
| `OptionLabeler` | Names each option: direction (`west`, `south`, `direct`) and kind (`shortest`, `positioning`, `coastal`). |
| `OptionProbabilityEstimator` | Share of members whose best route belongs to the option; ETA gap to the best option. |
| `OptionTimelineBuilder` | For one option: target position (zone centre + radius), heading, sail, TWA, TWS, speed at each horizon. |
| `ConfidenceGrader` | Share of the option's members inside the target zone → `high` / `medium` / `low`. |
| `ConsensusBuilder` | Circular median heading and majority sail of the option's members at a given time. |
| `AdviceWriter` | Rule-based advice as **i18n key + parameters** (never text), e.g. `advice.head_direction {option, count, total, hours}`. |

### `service` — application layer shared by the CLI and the API
| Class | Responsibility |
|---|---|
| `RoutePlanner` | Builds every object for one routing run (the only place that knows all engine layers) and returns a `RouteReport`; also provides the GFS wind for the map. |
| `RouteReport`, `ProjectPaths` | Result of one run; where data and caches live. |

### `api` — FastAPI
| Module | Responsibility |
|---|---|
| `app_factory.py` | Builds the app: routers under `/api`, frontend files at `/`. |
| `routes_races.py` | Race list, race file, boat polar. |
| `routes_routing.py` | `POST /api/route` (runs `RoutePlanner`), `GET /api/wind`. |
| `schemas.py` | Request models; converts settings to `BoatOptions`. |
| `route_result_builder.py` | `RouteReport` → result JSON (hourly path, plan steps, nulls while no ensemble). |
| `wind_grid_exporter.py` | `WindField` → leaflet-velocity grids for the map. |

### `frontend` — no build step, native ES modules
| Module | Responsibility |
|---|---|
| `src/main.js` (`App`) | Creates and connects the components; holds the current result and selected option. |
| `i18n/translator.js`, `i18n/language-picker.js` | Loads `i18n/<lang>.json`, translates keys; FR/EN toggle. |
| `storage/preferences-store.js` | Last race, boat, language in localStorage. |
| `form/position-parser.js`, `form/route-form.js` | Parses pasted positions; race/boat/position inputs, submit, one-line summary when collapsed. |
| `form/race-header.js`, `form/boat-picker.js` | From–to line with distance and live race status; boat class pills. |
| `results/data-refresh.js` | Time of the next data update (run every 6 h, usable ~4.5 h later). |
| `map/route-map.js` | Builds the Leaflet chart and its layers; the only map API the app uses. |
| `map/chart-basemap.js` | Nautical-chart background from `map-data/` (depth bands, land, coastline). No tile server. |
| `map/graticule-layer.js`, `map/sea-labels.js` | Degree grid with edge labels; italic sea names (i18n). |
| `map/course-layer.js` | Race course: start line of the chosen boat, gates, marks (IALA colours), finish, forbidden and vigilance zones. |
| `map/route-layer.js` | Ideal track to the finish (visual only), member routes, selected option, target zones, boat at the selected hour. |
| `map/wind-grid.js` | Bilinear wind lookup on a leaflet-velocity grid. |
| `map/wind-particles-layer.js`, `map/wind-barbs-layer.js` | Wind as animated particles (leaflet-velocity) or as meteorological barbs (canvas). |
| `map/map-controls.js`, `map/map-style.js` | View (48 h / whole race), hour chips, particles/barbs toggle, knots legend; pane stack and theme colours. |
| `how.html`, `src/how-main.js`, `how/how-page.js` | "How it works" page: data, refresh times, method, options, limits; text in i18n. |
| `layout/theme-toggle.js` | Light/dark switch; follows the system until the user picks, then remembers it. |
| `settings/settings-panel.js`, `settings/boat-options-form.js`, `settings/maneuver-times.js` | Settings dialog: owned sails one by one, editable manoeuvre times pre-filled from the VR polar (saved per boat); any change recomputes. |
| `layout/panel-collapser.js` | Collapses a floating panel out of the chart's way (form → summary line after computing, "now" panel → slides down, right column → slides right leaving a strip); click brings it back. |
| `results/now-panel.js` | "Set this now" as boat instruments, built from `results/instruments/`: compass dial (heading + wind direction), sail wardrobe, true-wind gauge with Beaufort force, speed dial. |
| `results/option-list.js` | Option cards with a probability ring. |
| `results/route-plan-list.js` | Route plan as orders: one row per leg (start, heading, sail, wind, duration) over 48 h; a leg selects its hour on the map. |
| `results/display-format.js`, `results/term-tip.js`, `dom.js` | Formatting (DMS, headings, decimals per language), jargon tooltips, DOM helper. |
| `api/api-client.js`, `api/route-computation.js` | Calls the backend; one computation = route then map wind. |

The response shape is documented in [api-contract.md](api-contract.md).

### `api`
| Module | Responsibility |
|---|---|
| `app_factory.py` | Builds the FastAPI app and wires all objects (the only place that knows every layer). |
| `routes_*.py` | One module per endpoint group (races, routing, weather status). |
| `schemas.py` | Pydantic request/response models. |

## Main data flow

```
user: race + boat + position text
  → PositionParser → GeoPoint
  → RaceCatalog → Race (next mark from position)
  → ForecastStore → EnsembleForecast (downloaded once per GEFS run)
  → EnsembleRouter → 31 GEFS routes + 1 GFS route
  → RouteOptionClusterer → OptionLabeler → OptionProbabilityEstimator
  → OptionTimelineBuilder (+ ConfidenceGrader, ConsensusBuilder) → AdviceWriter
  → JSON → frontend (now panel, option cards, route plan, map; text translated client-side)
```
