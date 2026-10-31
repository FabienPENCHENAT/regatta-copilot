# Architecture

Status: **planned** (step 1). Classes are created as the steps progress. Keep this page in sync with the code:
when a class is added, renamed or split, update the table.

## Repository layout

```
routeur-voile/
├── backend/sailrouter/     Python package (FastAPI + routing engine)
├── backend/tests/          pytest, mirrors the package layout
├── frontend/               Vite + vanilla JS + Leaflet
│   └── i18n/               fr.json, en.json (all UI text)
├── races/                  one JSON file per race (generic format, no code change to add a race)
├── data/polars/            VR polar JSON files (+ sources/ with provenance)
├── data/geo/               simplified coastline (Natural Earth)
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

### `ensemble` — the robust route
| Class | Responsibility |
|---|---|
| `EnsembleRouter` | Runs `IsochroneRouter` for each member (process pool), reports progress. |
| `PositionClusterer` | Groups member positions at T+5/24/48 h; returns the majority cluster. |
| `ConfidenceGrader` | Share of members in the majority cluster → green / orange / red. |
| `ConsensusBuilder` | Circular median of first headings, majority sail. |
| `AdviceWriter` | Rule-based advice as **i18n key + parameters** (never text), e.g. `advice.stay_south {n: 24, total: 31}`. |

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
  → EnsembleRouter → 31 Routes
  → PositionClusterer + ConfidenceGrader + ConsensusBuilder + AdviceWriter
  → JSON → frontend (map, 3 cards, advice sentence translated client-side)
```
