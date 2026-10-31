# Architecture

Status: **planned** (step 1). Classes are created as the steps progress. Keep this page in sync with the code:
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

### `domain` — pure value objects, no I/O
| Class | Responsibility |
|---|---|
| `GeoPoint` | Latitude/longitude pair, normalised. |
| `GreatCircle` | Distance, initial bearing and destination point on the sphere (vectorised). |
| `PositionParser` | Turns user text (`46°12'30"N 012°34'10"W`, `46.21, -12.57`, ...) into a `GeoPoint`. |
| `Mark`, `ExclusionZone`, `Race` | Course definition: ordered marks with passing side, finish, forbidden zones, allowed classes. |

### `course` — loading races
| Class | Responsibility |
|---|---|
| `RaceCatalog` | Lists and loads `races/*.json` into `Race` objects; validates the file. |

### `weather` — everything GFS/GEFS
| Class | Responsibility |
|---|---|
| `GfsRunClock` | Which run (00/06/12/18 UTC) is the latest complete one; when the next is expected. |
| `NomadsClient` | Builds NOMADS grib-filter URLs and downloads one file, throttled, with retries. |
| `GefsRunDownloader` | Downloads all members × lead times of a run through `NomadsClient`. |
| `GribDecoder` | GRIB2 bytes → U/V arrays + grid (ecCodes). |
| `ForecastStore` | On-disk cache of decoded runs (`var/weather/<run>.npz`), one download per run. |
| `WindField` | Wind for one member: bilinear in space, linear in time → TWS (kn), TWD (deg). Vectorised. |
| `EnsembleForecast` | The 31 `WindField`s of one run + run metadata. |

### `polar` — boat performance
| Class | Responsibility |
|---|---|
| `VrPolarParser` | Raw VR `Meta_GetPolar` JSON → `BoatPolar`. |
| `BoatPolar` | Speed tables per sail; bilinear lookup (TWS, TWA). |
| `BoatOptions` | Which options the player owns (sail packs, foils, hull, pro winch). |
| `SpeedModel` | Polar × options → best allowed sail and boat speed for many (TWS, TWA) at once. |
| `ManeuverPenalty` | Time lost on tack, gybe, sail change (V1: fixed, configurable; later: wind and energy). |

### `geography` — where the boat may not go
| Class | Responsibility |
|---|---|
| `CoastlineLoader` | Reads the simplified coastline into polygons. |
| `LandMask` | Fast raster lookup "is this point on land or in a forbidden zone?". |
| `ObstacleChecker` | Whether a segment between two points crosses land or a forbidden zone. |

### `routing` — one wind field, one route
| Class | Responsibility |
|---|---|
| `TimeSchedule` | Step durations: 1 h until T+24 h, 3 h beyond. |
| `HeadingFan` | Candidate headings (every 5°) from each front point. |
| `Isochrone` | One front: points, parent indices, sail, heading, time. |
| `IsochronePruner` | Keeps the best point per angular sector around the next mark. |
| `MarkProgress` | Which mark is next for each point; detects mark passing on the correct side. |
| `IsochroneRouter` | Runs the steps: expand → apply speed and penalties → drop obstacles → prune. |
| `RouteTracer` | Walks parents back from the best final point → `Route`. |
| `Route` | Ordered `RoutePoint`s (time, position, heading, TWA, TWS, sail, speed). |

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

### `frontend` — no build step, native ES modules
| Module | Responsibility |
|---|---|
| `src/main.js` (`App`) | Creates and connects the components; holds the current result and selected option. |
| `i18n/translator.js`, `i18n/language-picker.js` | Loads `i18n/<lang>.json`, translates keys; FR/EN toggle. |
| `storage/preferences-store.js` | Last race, boat, language in localStorage. |
| `form/position-parser.js`, `form/route-form.js` | Parses pasted positions; race/boat/position inputs and submit. |
| `map/route-map.js` | Builds the Leaflet chart and its layers; the only map API the app uses. |
| `map/chart-basemap.js` | Nautical-chart background from `map-data/` (depth bands, land, coastline). No tile server. |
| `map/graticule-layer.js`, `map/sea-labels.js` | Degree grid with edge labels; italic sea names (i18n). |
| `map/course-layer.js` | Race course: start line of the chosen boat, gates, marks (IALA colours), finish, forbidden and vigilance zones. |
| `map/route-layer.js` | Ideal track to the finish (visual only), member routes, selected option, target zones, boat at the selected hour. |
| `map/wind-grid.js` | Bilinear wind lookup on a leaflet-velocity grid. |
| `map/wind-particles-layer.js`, `map/wind-barbs-layer.js` | Wind as animated particles (leaflet-velocity) or as meteorological barbs (canvas). |
| `map/map-controls.js`, `map/map-style.js` | View (48 h / whole race), hour chips, particles/barbs toggle, knots legend; pane stack and theme colours. |
| `results/now-panel.js` | "Set this now": heading, sail, TWA, TWS, speed + advice sentence. |
| `results/option-list.js` | Option cards with probability. |
| `results/timeline-table.js` | Route plan table (cards on phones). |
| `results/display-format.js`, `results/term-tip.js`, `dom.js` | Formatting (DMS, headings, decimals per language), jargon tooltips, DOM helper. |
| `api/mock-api.js` | Mock-up stand-in; replaced by an `ApiClient` with the same interface in step 5. |

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
