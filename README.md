# Routeur Voile

Assistant de routage pour **Virtual Regatta Offshore**, robuste face à l'incertitude météo
(31 scénarios de l'ensemble NOAA GEFS). Routing advisor for Virtual Regatta Offshore, built on the 31 NOAA
GEFS ensemble members.

Status: UI mock-up done (real GFS wind, example routes); routing engine in progress.

## Run it / Lancer le site

```sh
./run.sh
```
Then open http://localhost:8000 (the script also prints the address to open on a phone on the same Wi-Fi).
Puis ouvrir http://localhost:8000 (le script affiche aussi l'adresse à ouvrir sur le téléphone, même Wi-Fi).

- Founder documentation (FR): [docs/founder/](docs/founder/)
- AI / developer documentation (EN): [docs/ai/index.md](docs/ai/index.md)

Data: NOAA GFS/GEFS (public domain), OpenStreetMap contributors (map tiles), Natural Earth (coastline).
