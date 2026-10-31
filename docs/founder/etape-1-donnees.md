# Étape 1 : vérification des données (31/10/2026)

## En bref

| Sujet | Résultat |
|---|---|
| Météo | **NOAA NOMADS (GEFS 0,5°)**, pas Open-Meteo : Open-Meteo épuiserait le quota en une grille. |
| Polaire Class40 | **La vraie polaire du jeu est disponible publiquement.** Plus besoin d'une polaire « approximative ». |
| Parcours | Plus riche que prévu : tour de **toute la Guadeloupe** à bâbord, avec 4 marques et environ 21 zones interdites. |
| Dépôt de référence | `keziah744/routeur-rhum` est très proche de notre idée, mais il n'a pas de licence : on s'en inspire sans copier. |

## 1. Météo

**Open-Meteo, mesuré :** chaque point coûte 6,2 unités de quota (2 variables × 31 scénarios), que ce soit sur
2 ou 10 jours. Limite : 600 unités par minute et environ 10 000 par jour.
Une grille Atlantique au 1° compte environ 4 400 points, soit environ 27 000 unités : **près de 3 jours de quota
pour une seule mise à jour.** Impossible.

**NOAA NOMADS, testé :** on demande uniquement le vent à 10 m, sur la zone 5–55°N / 80°W–5°E.
- 56 Ko par fichier en 0,5° (223 Ko en 0,25°).
- 31 scénarios × 41 échéances (5 jours) = 1 271 fichiers ≈ **72 Mo par run**, téléchargés une fois toutes les 6 h,
  en tâche de fond. Gratuit, sans quota (il faut juste ne pas envoyer trop de requêtes à la seconde).
- Décodage vérifié en Python, sans rien installer sur le Mac à part un paquet Python.
- Secours prêt : le même jeu de données est copié par la NOAA sur Amazon (sans limite de requêtes).

**À savoir :** les scénarios GEFS sont fournis **toutes les 3 h**, jamais toutes les heures. Entre deux, on
interpole. Le routeur, lui, avance quand même par pas de 1 h au début.

**Choix fait (le plus simple) :** 0,5° plutôt que 0,25°. C'est 4 fois moins lourd. À 24–48 h, l'écart entre
scénarios pèse bien plus que la finesse de la grille.

## 2. Polaire Class40

- Un site communautaire (vro.civis.net) publie les polaires du jeu dans le format brut de VR. Celle du Class40
  (`mono/class40-2021`, mise à jour VR du 02/07/2024) est enregistrée dans `data/polars/`.
- Elle contient 7 voiles : Jib (foc), Spi, Staysail (trinquette), LightJib (foc léger), Code0, HeavyGnk
  (gennaker lourd) et LightGnk (gennaker léger). Elle contient aussi le bonus foils (+4 % entre 80 et 160° du vent,
  de 16 à 35 nœuds), le bonus coque (+0,3 %) et les **vraies pénalités de manœuvre** : 3 à 5 min à 50 % de
  vitesse, ou 70 % avec le treuil « pro ».
- Une autre copie (ITYC) est plus ancienne (2023) et diffère : on ne la prend pas.
- Ce n'est pas vérifié dans le jeu. Pour comparer avec ton export, voir
  [extraire-polaire-vr.md](extraire-polaire-vr.md). L'import de ton JSON reste prévu dans « Réglages ».

## 3. Course Virtual Regatta

- Ta course : **Route du Rhum - Class40**, n° 844 dans VR.
- Départ le **dimanche 1er novembre 2026 à 12:02 UTC** (13:02 heure de Paris), c'est-à-dire **demain**.
- Fermeture le 30/11 à 13:00 UTC.
- VR estime 15 à 18 jours de course en Class40 : l'outil sera utile bien après le départ, même s'il n'est pas prêt
  demain.

**Correction du parcours :** les instructions de course 2026 demandent de faire **le tour de la Guadeloupe à
bâbord**, pas seulement de la Basse-Terre :
1. îlot Tête à l'Anglais à bâbord ;
2. bouée de Basse-Terre à tribord ;
3. les Saintes à tribord ;
4. bouée d'atterrissage de Pointe-à-Pitre contournée à bâbord ;
5. ligne d'arrivée sur 16°12' N, franchie vers le nord.

Le départ des Class40 se fait sur leur propre segment de ligne (48°43,5'–48°44,1' N, 1°54' W), avec la porte
de Fréhel juste après. Environ 21 zones interdites s'ajoutent : rails de navigation d'Ouessant, du Finisterre et
des Canaries, parcs éoliens, grande zone cétacés autour des Açores, Mauritanie, etc.

Je reprendrai ces coordonnées **dans les documents officiels** à l'étape 3, pas dans un autre dépôt.
**Les zones propres au jeu ne sont publiées nulle part** : il faudra que tu jettes un œil à la carte de la course
dans VR pour confirmer.

## 4. Dépôts existants

- **keziah744/routeur-rhum** (créé le 30/10) fait déjà, pour l'Ultim : GFS + 31 scénarios GEFS, isochrones, tour
  de la Guadeloupe, zones interdites, interface mobile. Ses limites par rapport à notre idée :
  - environ 1 h de téléchargement et 20 min de calcul par cycle d'ensemble ;
  - il choisit « la route la plus sûre » au lieu de montrer des zones avec un niveau de confiance ;
  - pas de bilingue, une seule course.
  Il n'a **aucune licence**, ce qui interdit de copier son code. On s'en inspire seulement.
- **toxcct/VRPolarsChart** est sous licence GPL-3.0 : idem, pas de copie de code. Son how-to repose sur l'extension
  VR Dashboard, aujourd'hui peu fiable, d'où la méthode sans extension du guide.
- **thibaro/ultimrouter**, **guime7000/MOwnR** et **Ricou2956/windyvr-lsv-team** n'ont pas de licence non plus.
  Ce sont des routeurs plus anciens ou un plugin Windy.

## 5. Ce qui est en place dans le dépôt

- Git initialisé (branche `main`, aucun dépôt distant).
- `docs/ai/` : documentation pour l'IA (architecture prévue classe par classe, conventions, décisions, sources).
- `docs/founder/` : cette documentation.
- `data/polars/` : la polaire Class40 et sa provenance.

## Question en attente

Voir la fin du message de l'étape 1 : faut-il ajouter la route GFS « officielle » (celle que voit le jeu) en plus
des 31 scénarios ?
