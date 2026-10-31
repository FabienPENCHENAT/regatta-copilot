# Conventions

## Classes and files

- **One class, one responsibility.** If describing a class needs "and", split it.
- **The name says what the class does**, as a noun for a thing (`PolarTable`, `WindField`) or an agent noun for
  a worker (`GefsDownloader`, `IsochronePruner`, `AdviceWriter`). No `Manager`, `Helper`, `Utils`, `Service`
  without a precise qualifier.
- **One public class per file**, file named after the class in snake_case (`wind_field.py` → `WindField`).
- **Size budget:** aim for < 150 lines per class, hard limit 250 per file. Over budget means a missing class.
- Methods short (< 30 lines), named with a verb (`speed_at`, `prune`, `download_run`).
- Prefer small immutable value objects (`@dataclass(frozen=True)`) for data passed between layers.

## Dependencies between layers

See [architecture.md](architecture.md). Dependencies only point **downwards**:
`api → ensemble → routing → (weather, polar, geography) → domain`.
- `domain` imports nothing from the project.
- `weather`, `polar`, `geography` never import each other.
- Only `api` knows about HTTP/FastAPI. Only `weather` knows about GRIB/NOMADS.
- Wire objects together in one place (`api/app_factory.py` or the CLI entry point), not inside classes.

## Python

- Python ≥ 3.12, type hints everywhere, `numpy` for anything in a hot loop (vectorise over points/headings).
- Units in names when ambiguous: `speed_kn`, `heading_deg`, `duration_s`, `lat_deg`.
- Angles in degrees at boundaries, radians only inside computations.
- Longitudes in [-180, 180).

## Frontend

- Vanilla JS modules (Vite). One module per UI component (`position-input.js`, `result-card.js`, `route-map.js`).
- **No hard-coded UI text.** Every string comes from `frontend/i18n/fr.json` / `en.json` (same keys in both).
- Accessible: labels on inputs, contrast AA, tooltips for jargon (TWA, TWS, VMG...).

## Tests

- `pytest`, one test file per class under test (`tests/weather/test_wind_field.py`).
- Required: position parser, wind interpolation, one isochrone on constant wind (known answer), coast collision.
- No network in tests: use small fixtures in `tests/fixtures/`.

## Git

- Small commits, imperative message in English (`Add PolarTable bilinear lookup`).
- Never push to a remote without the user's explicit agreement.
