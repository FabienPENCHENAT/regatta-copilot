# Decision log

Newest first. Format: decision, why, rejected alternatives. Mark decisions waiting for the user as **PENDING**.

## D50 — Time bar instead of hour chips; 5-day view (user, 2026-10-31)
- The hour chips (start, +4 … +48 h) become `map/TimeBar`: a slider over the whole route (0–120 h, hourly),
  a mark at each change of orders of the selected option (floored leg start hours), ◀ ▶ buttons jumping to
  the previous / next change, value "+12 h · sun. 01:02". Built once and updated in place (`MapControls` keeps
  it across renders) so a drag is not interrupted; the wind of an hour is fetched once the slider rests
  200 ms (`WIND_SETTLE_MS`), the nearest loaded hour is shown meanwhile.
- Stops (user): every hour until +24 h, then every 3 h (the GFS steps, and the route points beyond +48 h); no
  finer step. The slider moves stop by stop (`timeStops`), the first day taking 24 of the 57 stops; order
  marks are snapped to the stop at or before them. The view chips get a visible title "Cadrer sur" / "Frame on".
- New map view "5 j" (120 h). The boat heading at any hour comes from the leg sailed then (`legAt`).

## D49 — Option line drawn through every route point; boat picker on the polar page (user, 2026-10-31)
- Leg markers did not sit on the selected option's line near the start: the map drew the HOURLY `path`
  (straight cuts between hours) while legs change every 15 min. Options now carry `line` (every route point),
  which the map draws; `path` stays hourly for placing the boat at an hour. Checked: all leg starts lie on it.
- Polar page: the boat came silently from the saved preferences; it now shows the race's boats as pills
  (preselected on the map's boat), and switching reloads the curves.

## D48 — "Polar and options" page (user, 2026-10-31)
- `frontend/polar.html` (rail link): polar diagram (SVG, `polar/PolarChart`) at a chosen TWS, the player's
  options dashed, the tried options coloured by best sail (`--sail-<id>` tokens), TWA read-out (pointer or
  slider), gain summary (max and mean % between TWA 40–160°). `polar/OptionToggles` starts from the settings
  (`boatOptions`), marks owned ones ("à toi"); "Keep these options" writes the settings, nothing else does.
- `GET /api/races/{race}/boats/{boat}/polar/curves?tws=&sails=&foil=&hull=` → `polar/PolarCurves` on the same
  `SpeedModel` as the router (every 2°).
- "On your route": `POST /api/options-impact` → `service/OptionsImpact`: two GFS routes (current vs tried
  options) from the last saved position; gain = difference in distance to go at +24/+48/+120 h (≈ 10 s).
  Own manoeuvre times are sent only when both sides use the same winch (else the game's values for each).

## D47 — Headings every 1° over 220° around the mark bearing (user, 2026-10-31)
- `HeadingFan(1.0, 220.0)`: per front point, 221 headings centred on the bearing to its leg's target
  (`MarkProgress.bearing_to_target_deg`), like routers made for the game (eSail4VR: 220°, 1°). Was 72 headings
  every 5° over 360°. Orders can now be given to the degree.
- Dead ends (bay, mark to round) are not handled by a 360° fallback: user accepts the risk ("on le voit à
  l'avance"). Tests keep `HeadingFan(5.0, 360.0)`.
- `ObstacleChecker` tests the segment END first (one lookup) before sampling: most headings aimed at the coast
  are settled at once; same routes. Ensemble from the start: ≈ 41 s (was ≈ 30 s with 5°, 61 s before the
  endpoint shortcut). Possible later: 1° for the first 24 h only, coarser after.

## D46 — 1 nm coast margin, re-opened around gates (user, 2026-10-31)
- User: routes passing close to the coast here may touch land in the game (Natural Earth 1:10M ≠ the game's
  coast). `geography/CoastMargin` widens the land raster by `COAST_MARGIN_NM` = 1 (ellipse per cell, longitude
  width at the band's highest latitude), cached in `var/land/` (≈ 3 s once, then 0.7 s to load).
- `ObstacleChecker` with a `margin` mask: a segment may not enter the margin; a segment STARTING inside it (start
  line, anchorage) is only checked against real land, so the boat can get out.
- `geography/GateCorridors`: within 1 nm of every gate/line of the race, the margin is replaced by the real
  land again — committees place gates in navigable water; without this the 1 nm Fréhel gate kept 0.17 nm.
  Checked: Class40 and IMOCA routes from the start cross Fréhel at 48.712–48.713°N (north end).

## D45 — The game's weather timing: 3-hourly GFS, switch 3 h 40 after the cycle (user, 2026-10-31)
- Source: eSail4VR guide ("calcul du vent", "horaires et retards"), a router connected to the game. VR reads GFS
  0.25° every 3 h and interpolates linearly in time (per U/V component) then bilinearly in space; a run is
  picked up ≈ 3 h 40 after its cycle (first lead times on NOMADS).
- `LeadTimePlan.game()` (f000, f003… f384) replaces the hourly lead times for the game's route and the map;
  `GfsRunClock` GFS delay 3 h 40 (GEFS keeps 5 h). An incomplete newest run still falls back to the previous one.
- `ENGINE_VERSION` in the result cache key: stored results made with the old weather are recomputed.
- Rejected for now: mixing runs like the game does (the past step bracketing "now" kept from the previous run):
  the exact switch rule is not documented (user: too risky). Not modelled, by user choice: auto-sail 1.4 %
  overlap / boost, skipper energy (stated on the How it works page).

## D44 — Position typed in boxes, as shown in the game (user, 2026-10-31)
- One free-text field needed °, ', " and N/W typed by hand ("un peu complexe"). `form/PositionFields`: per axis,
  degrees / minutes / seconds boxes (numeric keypad, auto-advance when full or on space ° ' ") and a hemisphere
  button (N/S, E/O). Pasting a whole position in any box still works (`PositionParser`). The last position stays
  pre-filled, so usually only minutes and seconds change. Saved as the same DMS text as before.
- Rejected: fetching the boat position from the game (no public API; a reading browser extension was offered and
  declined by the user).

## D43 — A newer request cancels the older one; land checked only for possible winners (user, 2026-10-31)
- "Changing an option takes far more than 30 s": each settings change queued a full 31-member computation
  (≈ 30–40 s each, one at a time since D42), so three ticks cost ≈ 1 min 45.
- Page: settings and next-mark changes recompute 1.2 s after the last change (`SETTINGS_SETTLE_MS`), so a burst
  of ticks makes one request.
- Server: `api/RouteRequestLedger` numbers the player's requests. A request still waiting for the computation
  lock, or whose ensemble is running, stops as soon as a newer one arrives (`ComputationSuperseded` → **409**;
  running worker processes are terminated, pending members cancelled). The background pre-computation never
  supersedes, it only yields. Measured: 3 changes 3 s apart → two 409 within 9 s, only the last one computed.
- `IsochronePruner.prune(..., blocked)`: obstacles are checked only for candidates that can still win their
  sector, farthest first (rounds of 1, 4, 16... per sector), instead of all ≈ 50 000 segments per step. Same
  routes (checked identical on real members), ≈ 12–15 % faster per member.
- Rejected: coarser sectors (1°) for members — not reliably faster and visibly different routes (option plans
  come from member medoids). Remaining floor ≈ 25–30 s: 31 members on 4 performance + 6 efficiency cores.

## D42 — Finer time steps, one computation at a time, visible computing state (user, 2026-10-31)
- Orders can change at any time in the game: `TimeSchedule` now uses phases — 15 min until +6 h, 30 min until
  +24 h, 1 h until +48 h, 3 h after (108 isochrones over 120 h instead of 56). Legs start and last to the quarter
  hour at first ("+2 h 15", "1 h 45"). Ensemble ≈ 30–50 s (once per run and inputs, thanks to the result cache).
- Ticking several sails in a row launched several 31-member computations at once (plus the background
  pre-computation): 2–4 min each and no visible feedback (the race card, collapsed, hid the busy button). Now:
  one computation at a time on the server (`_COMPUTING` lock in `CachedRouteComputer`, cache re-checked after
  waiting); the page ignores answers to superseded requests and shows a "computing your route…" pill.

## D-NEXT — Backlog choices (user, 2026-10-31)
Not to do: routing all the way to the finish / ETA ("do not estimate something improbable"); online hosting
(single user, local is fine). Keep in mind for later: skipper energy (longer manoeuvres when tired). In progress:
Guadeloupe mark sides + next-mark choice, background GFS refresh + pre-computation, player polar import.

## D41 — The player's own polar (user, 2026-10-31)
- `POST /api/races/{race}/boats/{boat}/polar` takes the JSON the player copied from the game's network tab
  (raw polar, or any wrapper such as `LogEventResponse`). `polar/PlayerPolarReader` finds the shallowest object
  holding `sail`, `tws`, `twa` at any depth (also inside a JSON string, depth ≤ 8), checks 7 sails with ids 1–7,
  a `winch` block and that `VrPolarParser` accepts it (tables matching the axes, `foil`...), else 400 with the
  reason. **Only the polar object is stored** (the wrapper may hold session data):
  `var/polars/<race>-<boat>.vr.json`, git-ignored. `DELETE` removes it (back to the community polar).
- `service/BoatPolarLocator` decides the polar file for the GFS planner and the GEFS workers (player's first).
  `GET …/polar` returns the raw polar plus `_source` (`player` | `community`) and `_imported_at`.
- The result cache key holds the polar fingerprint (`community` or `player@<file mtime>`): an import or a
  removal gives fresh results.

## D40 — Background weather refresher; requests never wait for a GFS download (user, 2026-10-31)
- A new deterministic GFS run used to be downloaded inside `POST /api/route` (~100 s). Now
  `service/WeatherRefresher` runs in a daemon thread started with the app (FastAPI lifespan; off with
  `create_app(refresh_in_background=False)`, as in the tests), every 10 min: (a) `GfsWindSource.download_latest`
  for the route window **+ 12 h** (the window slides; files already on disk cost nothing, an incomplete newest
  run costs one probe request), (b) `EnsembleDownloadJob.ensure` (GEFS, unchanged, D30), (c)
  `LastRoutePrecomputer.precompute(weather_changed)`.
- Requests route on the newest GFS run **on disk** covering the window (`prefer_cached`); they download only when
  no candidate run (latest due + 2 older) is on disk, e.g. the very first start. A result made on an older run
  than the expected one still expires after 30 min (D34). The cache key now holds the GFS run actually used
  (instead of the expected one), so the pre-computation after a download finds a new key.
- The last request (`var/last_request.json`, also in memory) is computed again when the GFS or GEFS run changed
  (always on the first cycle after start-up, cheap when cached), and also at every cycle while it is less than
  6 h old: during the race the start is rounded to 30 min in the key, so a result goes stale every 30 min.
  A failed pre-computation is retried at the next cycle.
- `api/CachedRouteComputer` holds the cached computation, shared by the endpoint and the refresher. It lives in
  `api` rather than `service` because it builds the JSON result and uses the JSON result cache (both `api`);
  the refresher (`service`) only receives callables, so dependencies still point downwards.
- Rejected: downloading GFS in a second job class mirroring `EnsembleDownloadJob` (a thread per model, more
  state); one refresher thread is enough since the GEFS job already has its own thread.
- Limit: when no run is on disk at all, a request and the refresher may download the same GFS files at once
  (no cross-thread lock for GFS); it only happens on the very first start.

## D39 — Guadeloupe rounding marks as directed half-line gates; next mark chosen by the player (user, 2026-10-31)
- Point marks were 2-nm waypoints, with no side check. Each mark left to one side is now a `gate` whose line
  runs from the physical mark to land or open water, crossed in one direction: crossing it proves the side, with
  the existing gate logic (`MarkProgress`). `position` keeps the physical mark (map, and the router's target:
  `Mark.target`). Constructions (derived from the SI, Guadeloupe rounded to port = anticlockwise), status
  `derived`: Tête à l'Anglais to port → half-line from the islet west to 062°18'W, southbound; Basse-Terre buoy
  to starboard → buoy east to the coast, southbound (boat between buoy and coast); Les Saintes to starboard →
  061°36'W from 15°53.1'N to 16°00'N across the Canal des Saintes, eastbound (north of the archipelago);
  Pointe-à-Pitre landfall buoy to port → buoy east to 061°29.4'W, northbound. Checks in
  [data-sources.md](data-sources.md#course-route-du-rhum-2026).
- The `island` kind (skipped by the router) is gone: no race uses it any more; `point` stays a waypoint.
- Segments crossing the **finish** now stop on the line (`MarkProgress.end_at_finish`): the 1:10m land and the
  Pointe-à-Pitre spectator zone just north of it blocked every finishing segment, so no route could finish.
  The arrival time is still the end of the step (≤ 1 h late within 24 h, ≤ 3 h beyond).
- `NextMarkFinder` never auto-passes a rounding mark (`leave_to`): from anywhere around Guadeloupe it answers
  Tête à l'Anglais. The player picks the next mark: `POST /api/route` `next_mark` (id, or null = automatic,
  unknown id → 400); results carry `next_mark: {id, auto}`; the cache key holds `next_mark`.
- Synthetic check (constant 15 kn trade wind from 030°, 080°, 120°, 200°, 300°, from 17°N 60°W, real coast and
  zones): every route rounds the four marks in order on the right side and finishes in 16–20 h.

## D38 — Passed marks detected from the position (bug found 2026-10-31)
Routing from mid-Atlantic (45°N 12°W) sailed back towards the Fréhel gate (3 800 nm to go): the next mark was
only skipped with an explicit `--next-mark`. `routing/NextMarkFinder` now finds the first mark ahead: a gate or
line is passed when the position lies beyond it in its crossing direction by more than 2 nm; point and island
marks always count as ahead (to refine near Guadeloupe). Used by `MarkProgress.from_race` when no mark is given.

## D37 — All VR options back in the settings (user, 2026-10-31)
The user wants the site as close to the game as possible: foils, polished hull and pro winch are settings again
(off by default) and applied by the engine as in the game (foil bonus per boat polar). Manoeuvre times are
pre-filled for the owned winch level (std or pro) and overrides are saved per boat and winch level. The cache key
includes the equipment. Supersedes the "polar only" part of D29.

## D36 — At most 3 options (user, 2026-10-31)
A 4th option around 16–19 % was noise for the user. `RouteOptionClusterer(max_options=3)`: the smallest group
joins its nearest group, so its scenarios still count (probabilities still sum to 100 %). Stored results were
cleared (the cache key does not include synthesis settings: clear `var/results/` after changing them).

Measured effect of equipment, same GFS 06z run, Class40 start, 120 h (nm still to go; lower is better):
Jib+Spi only 2139 · +foils 2131 · +pro winch 2138 · +hull 2138 · +one optional sail 2136–2139 · +all five sails
2133 · full pack 2110 (≈ 29 nm, ≈ 2.4 h, ≈ 1.4 % over 5 days, mostly downwind under spinnaker). Gains are not
additive. The site keeps routing on owned sails and polar only (D29).

## D35 — Faster coast check: clearance map + length-grouped sampling (2026-10-31)
The land test sampled every candidate segment, all at the sample count of the longest one. Now `LandMask` keeps
a clearance map (distance to the nearest coarse land cell or raster edge, Chebyshev, in degrees, conservative):
a segment shorter than the clearance at one of its ends is skipped; the others are sampled in power-of-two
length groups. Measured from the Class40 start, 120 h, Jib + Spi: one route 4.4 s → 2.2 s (byte-identical
route); full ensemble request (31 members + GFS) 53.7 s → 24.2 s. A property test checks that every point within
the clearance of a sea point is at sea; it caught coarse cells sticking out of a fine raster whose size is not a
multiple of 16 (not the case for the real 0–60°N / 80°W–10°E area), now counted as edge.

## D34 — Results kept until the weather changes; most probable option stays recommended (user, 2026-10-31)
- The user pointed out that nothing changes between two forecast runs. Weather files were already cached per run;
  now computed results are too (`api/RouteResultCache`, `var/results/`), keyed by race, boat, position (4 dp),
  owned sails, manoeuvre times, start rounded to 30 min, expected GFS run and GEFS run. Same inputs → stored
  result (53 s → 0.02 s measured); a new run → new key → one fresh computation. A result made on an older GFS
  run than expected (fallback) expires after 30 min. Files older than 2 days are deleted.
- Recommendation stays "the most probable option" (largest group of scenarios): the user prefers the option most
  scenarios agree on, knowing it is updated at each run. The arrival gap (`eta_delta_h`) is no longer shown on the
  cards (each option is measured in its own weather, not comparable); cards show "n of 31 scenarios" instead.

## D33 — Option names, probabilities, confidence, arrival gap, advice (step 4, 2026-10-31)
- **Probability** = members of the option ÷ members routed (31; a member that cannot be routed is dropped).
  The GFS route never counts (D1). Recommended option = the most probable.
- **Id** from the option's **side of the consensus track** (start → median +48 h position of all members):
  cross-track gap of its representative route at +48 h + 2 × the gap at +24 h (same scale as the grouping,
  D32), positive to the right. The most central option is `direct` if its side is within 60 nm. The others,
  outermost first, take the compass name closest to their side of the consensus heading (westward course:
  right = `north`, left = `south`); a taken name falls to the next closest (45° steps), the heading's own
  direction first (`west`), no suffix. A single option is `consensus` / kind `consensus`.
  First version (rejected after the first real run): compass direction of the +48 h offset from the median
  position, named by probability; it called "east" an option that went south early on a westward course.
- **Kind**: `shortest` for the option whose +48 h position is closest (cross-track) to the great circle
  from the leg anchor to the next mark most members are heading for at +48 h; the others `positioning`.
  `coastal` is not produced.
- **Confidence** of a plan step = share of the option's members within the zone radius (3 + 0.9 × hour nm)
  of the representative position at that hour.
- **`eta_delta_h`** (approximation): arrival = hours sailed + distance to go at +120 h ÷ the route's own mean
  speed; gap to the earliest. Weather after +120 h is ignored.
- **Advice**: `advice.consensus {count, total, hours: 48}` for one option, else
  `advice.head_direction {option, count, total, hours: 48}`.
- i18n keys for these ids and kinds (`option.name.*`, `direction.*`, `option.kind*.consensus`,
  `advice.consensus`) and the `ensemble.*` status texts were added on the frontend side in parallel (main,
  commit 39adffc).

## D32 — Grouping member routes into options (step 4, 2026-10-31)
- Distance between two member routes = max(gap at +48 h, 2 × gap at +24 h): doubling the 24 h gap puts both
  horizons on the same scale (routes diverge about linearly), so routes that split early then cross are apart.
- Average-linkage agglomeration while the mean gap between two groups is ≤ 70 nm (middle of the 60–80 nm
  brief). Deterministic, ties to the lowest index. A group of one member joins its nearest group (a lone member
  is noise, not a scenario worth a card); then the smallest group merges into its nearest until ≤ 4 options.
  Rejected: k-means (needs k, random init), DBSCAN (leaves "noise" members outside every option).
- Each option shows its **medoid** member route (smallest total distance to the others): a real, sailable
  route with consistent legs, unlike an average of positions.
- `game_route` = the option holding the member nearest to the GFS route (same distance).

## D31 — 31 member routes in parallel processes (step 4, 2026-10-31)
`EnsembleRoutePlanner` uses a `ProcessPoolExecutor` with the **spawn** context (fork is unsafe inside the
threaded web server), cpu − 1 workers. Each worker builds the race, polar and land raster once
(`initialize`), then decodes its member's GRIB files from the cache and routes it (no wind field is pickled);
only the `Route` comes back. The GFS route (the game's) runs in the main process meanwhile, as before
(downloaded on demand). Same request for every member: position, owned sails, manoeuvre overrides, 120 h.
A new pool per request (≈ 1–2 s of start-up) keeps the code simple; a persistent pool would need per-boat
state.
Measured on the dev Mac (10 cores: 4 performance + 6 efficiency), Class40 from the start, 120 h: one member
alone 4.4 s, but ≈ 14 s each when 9 run at once (6 workers: same total); members 52 s, GFS route 15 s in
parallel, `POST /api/route` 53 s in all (target < 60 s met, barely). Profiling: 63 % of a route is the
land sampling of `ObstacleChecker._any_sample` (large temporary arrays, memory-bound, so processes slow each
other). Next lever, not done (outside step 4): a coarse "distance to land" raster to skip the sampling of
segments far from any coast.

## D30 — GEFS download in the background, once per run (step 4, 2026-10-31)
- NOMADS grib filter `filter_gefs_atmos_0p50a.pl`, `pgrb2ap5`, members `gec00` + `gep01..30`, UGRD/VGRD 10 m,
  0–60°N / 80°W–10°E (66 KB per file, measured). 3-hourly lead times bracketing the window
  [max(race start, now), +120 h] **plus 12 h**, so that the window sliding with time does not force a new
  download at every request. From the race start with the 06z run: 46 leads × 31 = 1 426 files ≈ 94 MB.
- The last lead time of every member is fetched first: an incomplete run fails within the first requests and
  the previous run is tried (newest due run = cycle + 5 h, then 2 older ones). A run found incomplete, or a
  network failure, is retried after 10 min.
- Sequential requests, at most 2 per second. Measured on the 2026-10-31 06z run: 1 426 files, 93 MB in
  14 min 48 s (≈ 1.6 files/s; NOMADS answers in ≈ 0.5–0.7 s).
  Cache `var/weather/gefs-YYYYMMDDHH/fFFF-<member>.grib2`, resumable file by file.
- Never inside a request: `POST /api/route` calls `EnsembleDownloadJob.ensure`, which answers with the newest
  complete run on disk (or none → GFS-only result) and starts a background thread when a newer run is due.
  `GET /api/ensemble/status` exposes the state; `python -m sailrouter ensemble-download` does the same in the
  foreground. A lock file (`var/weather/<run>.downloading`, stale after 120 s) stops the server and the CLI
  from downloading the same run twice.

## D29 — Polar-only routing, editable manoeuvre times, leg-based route plan, all Rhum boats (user, 2026-10-31)
- The user wants directions, not a full game simulation: the site routes on owned sails and each boat's polar
  speeds only. Foils, polished hull and pro winch are never applied (`BoatOptionsIn` has `sails` only; the CLI
  keeps `--options` for experiments).
- Manoeuvre times stay editable (user insisted): pre-filled from the polar `winch` block (standard winch), saved
  per boat in the browser, "reset to the game's values" button; sent as `maneuvers` and applied with
  `WinchTimings.with_overrides`. 0 disables a manoeuvre penalty.
- Route plan = legs, not fixed hours: `RouteLegSplitter` starts a new leg on a sail change, a tack/gybe, or a
  heading change ≥ 10° from the leg's first heading. Result field `options[].legs`.
- Polars for IMOCA (`mono/imoca_60_foils`, updated 2026-04-29), Ocean Fifty, Ultim BP XI and Vintage Multi
  (Happy) added from vro.civis.net; every Rhum boat now computes. Changing boat reloads its polar and recomputes.
- Map markers follow the route plan: one numbered point per leg start (same numbers as the plan rows, shared
  list from `results/plan-legs.js`); the hourly target-zone glows are gone until the ensemble brings confidence.

## D28 — Site wired to the engine; options per sail; VR manoeuvre times (user feedback, 2026-10-31)
- The user may own sails individually (not by pack): `BoatOptions(sails=frozenset, foil, hull, pro_winch)`;
  packs remain as CLI shorthands. The settings dialog has one checkbox per optional sail plus equipment.
- Manoeuvre times are no longer editable: they are read from the boat polar's `winch` block and displayed
  (std or pro winch, light ≤ lws / strong ≥ hws wind); the engine uses the same data. Skipper energy: not yet.
- "Compute my route" now runs the real engine: FastAPI app (`sailrouter/api/`) serving `/api/races`,
  `/api/races/{id}`, `/api/races/{id}/boats/{boat}/polar`, `POST /api/route`, `GET /api/wind`, and the frontend
  at `/`. `run.sh` starts uvicorn (installs `.venv` on first run). The mock API and mock data are removed.
- The planner moved from `cli/` to a `service/` layer (`RoutePlanner`, `RouteReport`, `ProjectPaths`) shared by
  the CLI and the API.
- Until the ensemble exists, a result has one option (`gfs`, the game's weather) with `probability: null` and
  step `confidence: null`; the UI shows "—" / "soon" instead of made-up figures. The page computes on load from
  the last position, and recomputes when owned options change.

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
