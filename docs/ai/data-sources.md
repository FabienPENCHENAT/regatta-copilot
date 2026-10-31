# Data sources

All checked on 2026-10-31 unless stated otherwise.

## Weather (GEFS)

**NOMADS grib filter, 0.5°** (chosen, see decisions D3):
```
https://nomads.ncep.noaa.gov/cgi-bin/filter_gefs_atmos_0p50a.pl
  ?dir=/gefs.YYYYMMDD/HH/atmos/pgrb2ap5
  &file=gepNN.tHHz.pgrb2a.0p50.fFFF        # gec00 = control, gep01..gep30 = perturbed
  &var_UGRD=on&var_VGRD=on&lev_10_m_above_ground=on
  &subregion=&toplat=55&leftlon=-80&rightlon=5&bottomlat=5
```
- Lead times `fFFF`: 000 to 240, every 3 h.
- Response: GRIB2, two messages (`10u`, `10v`, m/s), grid 101 × 171, first point 5°N / 280°E, step 0.5°.
- Use HTTP/1.1 (`curl --http1.1`): HTTP/2 requests to the NOMADS directory listing hung in tests.
- NOMADS bans clients that send too many requests per minute: throttle (≈ 1 request/s) and retry with backoff.
- Runs 00/06/12/18 UTC, complete ≈ 4–5 h later.

**AWS fallback**: `https://noaa-gefs-pds.s3.amazonaws.com/gefs.YYYYMMDD/HH/atmos/pgrb2sp25/gep01.tHHz.pgrb2s.0p25.f024`
(+ `.idx`; fetch `UGRD:10 m above ground` and `VGRD:...` with HTTP Range). Global, no subregion, no rate limit.

**Open-Meteo Ensemble** (rejected for the grid): `X-RateLimit-Cost` header = 6.2 per point for
2 variables × 31 members, limit 600/min. Fine for a handful of points (e.g. checking the wind at the boat).

Decoding: `pip install eccodes numpy` works on Python 3.14 (macOS arm64), no system library needed.

## Polars

`data/polars/class40-2021.vr.json`: VR polar `_id` 3 `mono/class40-2021`, `_updatedAt` 2024-07-02.
Source: `https://vro.civis.net/LSV-Dash/api?context=api&context_type=polars&boatType=mono/class40-2021`
(raw copy in `data/polars/sources/`). Same format as the game's `Meta_GetPolar` response:
- `tws` (16 values, kn), `twa` (31 values, deg), `sail[]` with `id`, `name`, `speed[twa][tws]` (kn).
- Sails: 1 Jib, 2 Spi, 3 Staysail, 4 LightJib, 5 Code0, 6 HeavyGnk, 7 LightGnk.
- `foil` (×1.04 for TWA 80–160°, TWS 16–35 kn, merge ramps 10° / 5 kn), `hull` (×1.003),
  `winch` (tack / gybe / sailChange: timers and speed ratios, std vs pro, light vs heavy wind 10/30 kn),
  `autoSailChangeTolerance` 1.014, `badSailTolerance` 1.02.
- An ITYC copy (`https://www.ityc.fr/data/export/class40-2021.json`) is **older** (2023-07-03) and differs.

Race ↔ boat mapping (third-party list `context_type=races`): VR race **844.1 "Route du Rhum - Class40"**,
boat `mono/class40-2021`, start 2026-11-01T12:02Z, end 2026-11-30T13:00Z. Other Rhum classes: 797.1 Ultim
(`Ultim BP XI`), 845.1 IMOCA (`mono/imoca_60_foils`), 846.1 Ocean Fifty (`multi/multi_50`), 847.1 Vintage Multi (`Happy`).

## Course (Route du Rhum 2026)

Official sources: sailing instructions 2026 with amendments, skipper Drive linked from
https://www.routedurhum.com/espace-skippers. To be turned into `races/route-du-rhum-2026.json` in step 3,
**re-checked against those documents** (not copied from another repo). Key facts to verify:
- Start line along 001°54.000'W, crossed westward; Class40 segment 48°43.500'N–48°44.100'N.
- Fréhel gate (002°18.500'W, 48°41.8'–48°42.8'N), westbound.
- Round **Guadeloupe** to port (not only Basse-Terre); Tête à l'Anglais to port; Basse-Terre buoy to starboard;
  Les Saintes to starboard; Pointe-à-Pitre landfall buoy rounded to port; finish line on 16°12.000'N, northbound.
- About 21 forbidden zones (traffic separation schemes, wind farms, Azores cetacean zone, Mauritania...).
- VR in-game zones and gates are **not public**: compare in the game.

## Coastline

Natural Earth 1:10m land (public domain), to be downloaded in step 3.

## Reference repositories

| Repo | Licence | Note |
|---|---|---|
| keziah744/routeur-rhum | none | Very close idea (Ultim). GFS 0.25 + GEFS 0.5 via NOMADS, GSHHG coast. Ensemble run ≈ 1 h download + 20 min compute. |
| toxcct/VRPolarsChart | GPL-3.0 | Polar viewer; how-to for extracting `Meta_GetPolar`. |
| thibaro/ultimrouter, guime7000/MOwnR | none | Older VR routers (2022–2023). |
| Ricou2956/windyvr-lsv-team | none | Windy plugin. |
