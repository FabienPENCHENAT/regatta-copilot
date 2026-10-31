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
with `start_line` and `polar`, ordered `marks[]` (`gate` with `points` + `cross`, or `point`/`island` with
`position` + `leave_to`), `finish`, `exclusion_zones[]` and `vigilance_zones[]` (`shape`: `polygon` | `line`,
`points` as `[lat, lon]`). Mark names are i18n keys `mark.<id>`.

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
"maneuvers": { "tack": { "light_min", "strong_min", "speed_percent" }, "gybe": {...}, "sailChange": {...} } }`
(optional sails among LightJib, LightGnk, Staysail, HeavyGnk, Code0; Jib and Spi are always allowed; foils, hull
and pro winch are never applied; missing maneuvers use the polar's standard-winch values).
One synchronous call. The route window is [max(race start, now), +120 h].
- **GEFS run on disk** → ensemble result (31 member routes + the GFS route, ≈ 53 s on the dev Mac, see D31).
- **Otherwise** → GFS-only result (~5 s, ~2 min the first time a GFS run is downloaded), and the GEFS download
  starts in the background (≈ 15 min, `ensemble.state = "downloading"`). Poll `GET /api/ensemble/status` and
  recompute when it says `ready`.

Each option has `legs`: `[{ start_hour, end_hour, heading_deg, sail, twa_deg, tws_min_kn, tws_max_kn, speed_kn,
lat, lon, end_lat, end_lon }]` (one per order: new leg on sail change, tack/gybe or heading change ≥ 10°).

**GFS-only result** (ensemble not ready): `weather.model = "GFS 0.25°"`, `weather.member_count = 1`, one option
`{ "id": "gfs", "kind": "game", "member_count": 1, "probability": null, "game_route": true }`, step
`"confidence": null`, `"members": []`, `advice = { "key": "advice.follow_game_route", "params": { "hours": 48 } }`.

**Ensemble result**: 1 to 4 options, most probable first.
- `id`: `consensus` when there is a single option, else unique among `direct` (the most central option, on
  the members' consensus track), `north`, `south` (its side of that track on a westward course), then `west`,
  `east` when two options share a side (decision D33) → i18n `option.name.<id>`.
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

**Both results** carry `"ensemble": { "state": "ready" | "downloading" | "unavailable", "run": ISO | null,
"done": int, "total": int, "member_count": 31 }` (same object as `GET /api/ensemble/status`). While a newer run
downloads, an older run on disk may still serve the ensemble result: `weather.run` is the run used,
`ensemble.run` the run being downloaded.

Response (ensemble):
```jsonc
{
  "race_id": "route-du-rhum-2026", "boat_id": "class40",
  "position": { "lat": 48.73, "lon": -1.9 },
  "computed_at": "2026-11-01T12:02:00Z",
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
The raw VR polar of the boat (the frontend reads its `winch` block to show manoeuvre times).
