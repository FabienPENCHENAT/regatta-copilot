# API contract

Served by `backend/sailrouter/api/` (FastAPI). Interactive docs at `/api/docs` when the server runs.


## `GET /api/races`
```json
[{ "id": "route-du-rhum-2026", "boats": ["class40", "imoca", "ocean_fifty", "ultim", "vintage_multi"],
   "default_boat": "class40" }]
```
Display names come from i18n keys `race.<id>` and `boat.<id>`.

## `GET /api/races/<id>`
The content of `races/<id>.json` (see [route-du-rhum-2026.json](../../races/route-du-rhum-2026.json)): `boats[]`
with `start_line` and `polar`, ordered `marks[]`, `finish`, `exclusion_zones[]` and `vigilance_zones[]` (`shape`:
`polygon` | `line`, `points` as `[lat, lon]`). Mark names are i18n keys `mark.<id>`.

Marks (decision D39):
```jsonc
// a gate or line to cross (Fréhel): no leave_to, no position → draw the line and its two ends
{ "id": "frehel_gate", "type": "gate", "points": [[48.696667, -2.308333], [48.713333, -2.308333]],
  "cross": "westward", "status": "official", "note": "..." }
// a mark rounded to one side (Guadeloupe): a directed half-line from the physical mark
{ "id": "tete_anglais", "type": "gate", "points": [[16.380833, -61.764167], [16.380833, -62.3]],
  "cross": "southward",            // southward | northward | eastward | westward
  "leave_to": "port",              // port | starboard
  "position": [16.380833, -61.764167],  // the physical mark: show THIS (buoy / islet / archipelago), not the line
  "status": "derived", "note": "..." }
```
Every Route du Rhum mark after Fréhel has `leave_to` and `position`: `tete_anglais`, `basse_terre_buoy`,
`les_saintes`, `pointe_a_pitre_buoy` (the `point`/`island` types are no longer used; `point` remains valid with
`position` only). The finish stays `finish.line` + `cross`.

## `GET /api/wind?start=<ISO UTC>[&hours=11,13]`
`hours` (optional, TODO backend after the step-4 merge): only these hours after `start`; default 0,4,8,12,16,24,48.
Deterministic GFS wind (the game's weather) for the map, in leaflet-velocity format (U record then V record,
m/s, rows north to south):
```jsonc
{ "model": "GFS 0.25°", "run": "2026-10-31T06:00:00Z", "start": "2026-11-01T12:00:00Z",
  "times": [{ "hour": 0, "grid": [{ "header": { "parameterNumber": 2, "nx": 71, "ny": 53, "lo1": -30, "la1": 56,
    "dx": 0.5, "dy": 0.5, ... }, "data": [...] }, { "header": { "parameterNumber": 3, ... }, "data": [...] }] }] }
```

## `POST /api/route`
Request: `{ "race_id", "boat_id", "position": { "lat", "lon" }, "options": { "sails": ["Code0", ...] },
"maneuvers": { "tack": { "light_min", "strong_min", "speed_percent" }, "gybe": {...}, "sailChange": {...} },
"next_mark": "<mark id>" | null, "current_route": { "path": [[lat, lon], ...] } | null }`.
`current_route` (optional, 1–200 points): the rest of the route the player has been following (the option of the
previous computation from another position, recognised by the page), from just after `position`. It is sailed
in the 31 weathers like the options, which are then compared with it (decision D60).
`next_mark` (optional, default null = automatic): the next mark to sail to, any id of `marks[]` or `"finish"`;
the marks before it are considered passed. Unknown id → **400** `{"detail": "unknown mark 'x' (known: ...)"}`.
Automatic: gates/lines without `leave_to` are skipped once the position is > 2 nm beyond them in their crossing
direction; a mark with `leave_to` is never skipped automatically (around Guadeloupe the automatic answer stays
`tete_anglais`: the player must choose).
(optional sails among LightJib, LightGnk, Staysail, HeavyGnk, Code0; Jib and Spi are always allowed; foils, hull
and pro winch are never applied; missing maneuvers use the polar's standard-winch values).
One synchronous call. The route window is [max(race start, now), +120 h].
- A newer `POST /api/route` arriving before this one is computed → **409** `{"detail": "a newer route request
  replaced this one"}` (D43); the page ignores answers to superseded requests anyway.
- Same inputs (incl. `next_mark` and the polar in use) on the same weather runs as an earlier request, or as the
  background pre-computation of the last request (D40) → the stored result at once.
- **GEFS run on disk** → ensemble result (31 member routes + the GFS route, ≈ 25–40 s on the dev Mac).
- **Otherwise** → GFS-only result (~5 s), and the GEFS download starts in the background (≈ 15 min,
  `ensemble.state = "downloading"`). Poll `GET /api/ensemble/status` and recompute when it says `ready`.
- The GFS run is the newest one **on disk** (the background refresher downloads new runs): no request waits for
  a GFS download, except when no run at all is on disk (first start, ~2 min). A result made on an older run than
  the expected one expires after 30 min.

Each option has `path` (one [lat, lon] per hour, for placing the boat at an hour), `hourly` (aligned with `path`:
what is sailed at each hour, `{ heading_deg, twa_deg, tws_kn, sail, speed_kn }` like `now`, shown in the boat's map
label at any hour; the last hour repeats the last leg's), `line` (every route point,
quarter-hours at first: what the map draws, so leg starts lie on it) and `legs`: `[{ start_hour, end_hour, heading_deg, sail, twa_deg, tws_min_kn, tws_max_kn, speed_kn,
lat, lon, end_lat, end_lon }]` (one per order: new leg on sail change, tack/gybe or heading change ≥ 10°).

**GFS-only result** (ensemble not ready): `weather.model = "GFS 0.25°"`, `weather.member_count = 1`, one option
`{ "id": "gfs", "kind": "game", "member_count": 1, "probability": null, "game_route": true }`, step
`"confidence": null`, `"members": []`, `advice = { "key": "advice.follow_game_route", "params": { "hours": 48 } }`.

**Ensemble result**: 1 to 4 options, most probable first.
- `outlook` (ensemble only): `[{ hours: 48|120, to_go_nm, gain_nm, worst_nm, ahead_share }]`: the option's
  track sailed in each of the 31 weathers (D55); `gain_nm` / `worst_nm` vs the reference, positive = ahead.
  The reference is given by `outlook_reference`: `"current_route"` when the request had one, else
  `"recommended"`. `current_route`: `{ outlook: [...] }` (its own distances to go, gains 0) or null.
- `id`: `consensus` when there is a single option, else unique among `direct` (nearest the line boat → next
  mark), and on each side of that line the compass name of the side (`north`/`south` on a westward course,
  `west`/`east` on a southward one), the next options on that side `<name>_wide` then `<name>_far` (decision
  D60) → i18n `option.name.<id>`. The page lists options by id (north to south), not in this order.
- `kind`: `consensus` (single option), `shortest` (closest to the great circle to the next mark at +48 h) or
  `positioning`.
- `probability` = `member_count` / members routed (31); `recommended_option` = the first option.
- `representative_member`: the GEFS member (`c00`, `p01`..`p30`) whose route is shown for the option (medoid).
- `steps[].confidence`: share (0–1, 2 decimals) of the option's members within `zone_radius_nm` of the step
  position.
- `eta_delta_h`: approximate arrival gap vs the best option (hours sailed + distance to go ÷ mean speed).
- `dtf_end_nm`: distance to go at the end of the representative route (+120 h).
- `game_route: true` on the option whose members are nearest the GFS route at +24/+48 h.
- `advice`: one option → `{ "key": "advice.consensus", "params": { "count", "total", "hours": 48 } }`;
  several → `{ "key": "advice.head_direction", "params": { "option", "count", "total", "hours": 48 } }`.
- `members`: one entry per routed GEFS member, `{ "member": "p07", "option": "west", "path": [[lat, lon], ...] }`,
  hourly from the start to +120 h, 3 decimals (≈ 31 × 121 points).
- `ideal_route`: the GFS route's full track (`path`, `distance_nm`, `to_go_nm`, `finished`), as before.
- `weather`: `{ "model": "GEFS 0.5°", "run", "game_model": "GFS 0.25°", "game_run", "next_run_expected",
  "member_count": 31 }`.

**Both results** carry `"next_mark": { "id": "<mark id used>", "auto": true | false }` (`auto` = found from the
position, false = the request's `next_mark`) and `"ensemble": { "state": "ready" | "downloading" | "unavailable", "run": ISO | null,
"done": int, "total": int, "member_count": 31 }` (same object as `GET /api/ensemble/status`). While a newer run
downloads, an older run on disk may still serve the ensemble result: `weather.run` is the run used,
`ensemble.run` the run being downloaded.

Response (ensemble):
```jsonc
{
  "race_id": "route-du-rhum-2026", "boat_id": "class40",
  "position": { "lat": 48.73, "lon": -1.9 },
  "computed_at": "2026-11-01T12:02:00Z",
  "next_mark": { "id": "frehel_gate", "auto": true },
  "weather": { "model": "GEFS 0.5°", "run": "2026-10-31T06:00:00Z", "game_model": "GFS 0.25°",
               "game_run": "2026-10-31T06:00:00Z", "next_run_expected": "2026-10-31T17:00:00Z", "member_count": 31 },
  "ensemble": { "state": "ready", "run": "2026-10-31T06:00:00Z", "done": 1302, "total": 1302, "member_count": 31 },
  "recommended_option": "west",
  "advice": { "key": "advice.head_direction", "params": { "option": "west", "count": 17, "total": 31, "hours": 48 } },
  "options": [{
    "id": "west",                 // i18n option.name.<id>
    "kind": "positioning",        // consensus | shortest | positioning → i18n option.kind.<kind>
    "member_count": 17,
    "probability": 0.548,
    "game_route": true,
    "eta_delta_h": 0.0,
    "representative_member": "p12",
    "dtf_end_nm": 2410,
    "now": { "heading_deg": 265, "twa_deg": 146, "tws_kn": 10.2, "sail": "Spi", "speed_kn": 7.5 },
    "steps": [{ "hour": 4, "lat": 47.21, "lon": -7.808, "heading_deg": 248, "twa_deg": 87,
                "tws_kn": 19, "sail": "Jib", "speed_kn": 11.6, "confidence": 0.94, "zone_radius_nm": 7 }],
    "path": [[48.73, -1.9], [48.8, -2.1]],
    "hourly": [{ "heading_deg": 265, "twa_deg": 146, "tws_kn": 10.2, "sail": "Spi", "speed_kn": 7.5 }, ...],
    "legs": [{ "start_hour": 0, "end_hour": 2.0, "heading_deg": 290, "sail": "Jib", ... }]
  }],
  "members": [{ "member": "c00", "option": "west", "path": [[48.73, -1.9]] }],
  "ideal_route": { "path": [[48.73, -1.9]], "distance_nm": 812, "to_go_nm": 2730, "finished": false }
}
```

Conventions: `twa_deg` signed (positive = wind on starboard), sail ids are the VR polar names
(`Jib`, `Spi`, `Staysail`, `LightJib`, `Code0`, `HeavyGnk`, `LightGnk` → i18n `sail.<id>`),
horizons are 4, 8, 12, 16, 24, 48 h.

## `GET /api/ensemble/status`
```json
{ "state": "downloading", "run": "2026-10-31T12:00:00Z", "done": 512, "total": 1426, "member_count": 31 }
```
`total` counts member × lead-time files (the download covers the window + 12 h); `run` is null when
`unavailable` (no run on disk and no download running, e.g. NOMADS unreachable: retried after 10 min).

## `GET /api/races/{id}/boats/{boat}/polar`
The raw VR polar the boat sails with (the frontend reads its `winch` block to show manoeuvre times), plus two
top-level fields:
```jsonc
{ "label": "mono/class40-2021", "tws": [...], "twa": [...], "sail": [...], "winch": {...}, ...,
  "_source": "player",                       // "player" (imported by the player) | "community" (data/polars/)
  "_imported_at": "2026-10-31T17:40:12.123456Z" }  // null for the community polar
```
404 for an unknown race or boat.

## `POST /api/races/{id}/boats/{boat}/polar`
Body: the JSON copied from the game's network tab, as is: the raw polar object, or any wrapper (e.g. a
`LogEventResponse`) holding it at any depth, even as a JSON string. The polar is the first object with `sail`,
`tws` and `twa`. Checked: 7 sails with ids 1–7, speed tables matching the TWS/TWA axes, `winch` and `foil`
blocks. Only the polar object is stored (`var/polars/<race>-<boat>.vr.json`), never the wrapper.
- 200 → same body as `GET` (`_source: "player"`). From now on every route of this race/boat uses it (GFS and the
  31 members), and stored results are not reused (the polar is part of the cache key).
- 400 → `{"detail": "invalid polar: <reason>"}`, e.g. `no VR polar found: expected an object with 'sail', 'tws'
  and 'twa'`, `the polar must have 7 sails`, `the polar has no 'winch' block (manoeuvre times)`,
  `the polar misses the field 'foil'`, `the polar tables are not consistent: ...`.
- 404 → unknown race or boat.

## `DELETE /api/races/{id}/boats/{boat}/polar`
Removes the player's polar (no error if there is none) and returns the polar now in use, same body as `GET`
(`_source: "community"`).


## `GET /api/races/{race}/boats/{boat}/polar/curves`
Query: `tws` (comma-separated, 1–12 values, 0–70 kn), `sails` (optional sails owned), `foil`, `hull` (bool).
→ `{ "twa": [0, 2, … 180], "curves": [{ "tws", "speed": [kn…], "sail": [sail id…] }] }` (best allowed sail).

## `POST /api/options-impact`
`{ race_id, boat_id, position, current: <options>, changed: <options>, maneuvers, next_mark }` → `{ start, run,
"gains": [{ "hours": 24|48|120, "gain_nm" }] }`; positive = `changed` is ahead. Two GFS routes, ≈ 10 s.
