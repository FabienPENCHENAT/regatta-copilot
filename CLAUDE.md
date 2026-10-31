# Routeur Voile

Read [docs/ai/index.md](docs/ai/index.md) first: it is the entry point for any AI agent working on this repo
(purpose, architecture, conventions, decisions, data sources).

Hard rules, repeated here because they are easy to break:
- Weather: NOAA GFS / GEFS only. Never ECMWF or any other model (the game uses GFS).
- The tool only advises. Nothing may play, click or send orders in the game on the user's behalf.
- Code and comments in English. UI text only in `frontend/i18n/*.json` (FR + EN), never hard-coded.
- One class = one responsibility, named after what it does. See [docs/ai/conventions.md](docs/ai/conventions.md).
- Talk to the user in French. Never push to a remote without asking.
