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

## `GET /api/wind?start=<ISO UTC>`
Deterministic GFS wind (the game's weather) for the map, in leaflet-velocity format (U record then V record,
m/s, rows north to south):
```jsonc
{ "model": "GFS 0.25°", "run": "2026-10-31T06:00:00Z", "start": "2026-11-01T12:00:00Z",
  "times": [{ "hour": 0, "grid": [{ "header": { "parameterNumber": 2, "nx": 71, "ny": 53, "lo1": -30, "la1": 56,
    "dx": 0.5, "dy": 0.5, ... }, "data": [...] }, { "header": { "parameterNumber": 3, ... }, "data": [...] }] }] }
```

## `POST /api/route`
Request: `{ "race_id", "boat_id", "position": { "lat", "lon" }, "options": { "sails": ["Code0", ...], "foil", "hull", "pro_winch" } }`
(optional sails among LightJib, LightGnk, Staysail, HeavyGnk, Code0; Jib and Spi are always allowed).
One synchronous call (~5 s, ~2 min the first time a GFS run is downloaded).

Until the ensemble exists: one option `{ "id": "gfs", "kind": "game" }`, `"probability": null`, step
`"confidence": null`, `"members": []`, and `ideal_route` = the computed 120 h track with `distance_nm`, `to_go_nm`, `finished`.

Response:
```jsonc
{
  "race_id": "route-du-rhum-2026", "boat_id": "class40",
  "position": { "lat": 47.5, "lon": -6.75 },
  "computed_at": "2026-11-02T10:12:00Z",
  "weather": { "model": "GEFS 0.5°", "run": "2026-11-02T00:00:00Z",
               "next_run_expected": "2026-11-02T10:30:00Z", "member_count": 31 },
  "next_mark": { "id": "guadeloupe_tete_anglais" },
  "recommended_option": "west",
  "advice": { "key": "advice.head_direction", "params": { "option": "west", "count": 17, "total": 31, "hours": 48 } },
  "options": [{
    "id": "west",                 // i18n option.name.<id>, direction.<id>
    "kind": "positioning",        // shortest | positioning | coastal → i18n option.kind.<kind>
    "member_count": 17,           // members whose best route is this option
    "probability": 0.55,          // member_count / member_count total
    "game_route": true,           // the deterministic GFS route (the game's weather) belongs to this option
    "eta_delta_h": 0.0,           // arrival gap vs the best option
    "dtf_48h_nm": 2961,           // distance to finish at +48 h
    "now": { "heading_deg": 265, "twa_deg": 146, "tws_kn": 10.2, "sail": "LightGnk", "speed_kn": 7.5 },
    // path: one point per hour from the start (the map places the boat at path[hour])
    "steps": [{ "hour": 4, "lat": 47.21, "lon": -7.808, "heading_deg": 248, "twa_deg": 87,
                "tws_kn": 19, "sail": "Code0", "speed_kn": 11.6, "confidence": 0.94, "zone_radius_nm": 14 }],
    "path": [[47.5, -6.75], [47.28, -7.54]]
  }],
  "members": [{ "option": "west", "path": [[47.5, -6.75]] }]
}
```
Conventions: `twa_deg` signed (positive = wind on starboard), sail ids are the VR polar names
(`Jib`, `Spi`, `Staysail`, `LightJib`, `Code0`, `HeavyGnk`, `LightGnk` → i18n `sail.<id>`),
horizons are 4, 8, 12, 16, 24, 48 h.

## `GET /api/races/{id}/boats/{boat}/polar`
The raw VR polar of the boat (the frontend reads its `winch` block to show manoeuvre times).
