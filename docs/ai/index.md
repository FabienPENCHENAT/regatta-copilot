# AI documentation: index

This folder is written for AI agents (and developers) working on the code. It is meant to spare them a full
re-exploration of the repo. The founder's own documentation, in French, lives in [../founder/](../founder/).

## What the product is

A web advisor for **Virtual Regatta Offshore** (VR). Given a pre-configured race, a boat class and the player's
current position, it says where to be in **5 h, 24 h and 48 h**, which **heading** and **sail** to use, with a
**confidence level**.

Differentiator: the route is computed on each of the **31 GEFS ensemble members**, and the advice is the zone
where most routes agree ("robust route"), not one optimal route that changes every 6 h.

First race: Route du Rhum 2026, Class40 (VR race 844, start 2026-11-01 12:02 UTC).

## Pages

| Page | Content |
|---|---|
| [architecture.md](architecture.md) | Layers, packages, classes and their single responsibility. Data flow. |
| [conventions.md](conventions.md) | Naming, class size, dependencies, tests, i18n, commits. |
| [decisions.md](decisions.md) | Decision log (what was chosen, why, what was rejected). |
| [data-sources.md](data-sources.md) | Weather, polar, coastline, course: URLs, formats, measured costs, licences. |

## Status

| Step | State |
|---|---|
| 1. Data verification | done (see [../founder/etape-1-donnees.md](../founder/etape-1-donnees.md)) |
| 2. Static UI mock-up (FR/EN) | next |
| 3. Routing POC, one member, CLI | todo |
| 4. Ensemble + robust synthesis | todo |
| 5. Wire UI, tests, README FR/EN | todo |

## Non-negotiable rules

- GFS/GEFS only. The game uses NOAA GFS; a "better" model is useless here.
- Advice only. No automation of the game.
- Free sources only. Credit OpenStreetMap, Open-Meteo (if used), NOAA in the UI.
- Do not copy code from the reference repos: none of them has a licence compatible with copying
  (see [data-sources.md](data-sources.md#reference-repositories)).
