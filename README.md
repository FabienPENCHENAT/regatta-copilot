# Routeur Voile

Assistant de routage pour **Virtual Regatta Offshore**, robuste face à l'incertitude météo
(31 scénarios de l'ensemble NOAA GEFS). Routing advisor for Virtual Regatta Offshore, built on the 31 NOAA
GEFS ensemble members.

Status: UI mock-up done (real GFS wind, example routes); routing engine for one weather member works from the
command line (step 3). Next: 31-member ensemble (step 4), then wiring the UI to the engine (step 5).

## Compute a route (command line)

```sh
python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt -e backend
.venv/bin/python -m sailrouter route --race route-du-rhum-2026 --boat class40 --position "48°43'48\"N 001°54'00\"W" --hours 120
.venv/bin/python -m pytest backend
```

## Run it / Lancer le site

```sh
./run.sh
```
Then open http://localhost:8000 (the script also prints the address to open on a phone on the same Wi-Fi).
Puis ouvrir http://localhost:8000 (le script affiche aussi l'adresse à ouvrir sur le téléphone, même Wi-Fi).

- Founder documentation (FR): [docs/founder/](docs/founder/)
- AI / developer documentation (EN): [docs/ai/index.md](docs/ai/index.md)

Data: NOAA GFS/GEFS (public domain), Natural Earth (coastline, depths), Leaflet (map library).
