# Étape 3 : premier calcul de route (31/10/2026)

## En bref

Le moteur de routage existe et calcule une vraie route pour la Route du Rhum, en Class40 :

- avec **la météo du jeu** (le modèle GFS de la NOAA, un seul scénario pour l'instant) ;
- avec **la vraie polaire VR du Class40**, toutes les options activées (voiles, foils, coque, winchs pro) ;
- en contournant **les côtes et les 22 zones interdites** des instructions de course ;
- en passant la **porte de Fréhel** dans le bon sens.

Il s'utilise pour l'instant **en ligne de commande** (dans le Terminal), sans écran. Le calcul prend environ
**6 secondes** pour 5 jours de course. L'écran (étape 5) et les 31 scénarios GEFS (étape 4) viendront ensuite.

## Le lancer en une commande

La première fois seulement, installer l'outil (depuis le dossier du projet) :

```
/opt/homebrew/bin/python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt -e backend
```

Puis, à chaque fois :

```
.venv/bin/python -m sailrouter route --position "48°43'48\"N 001°54'00\"W" --hours 120
```

- `--position` : ta position, copiée du jeu (`48°43'48"N 001°54'00"W`) ou en décimal (`48.73, -1.9`).
  Les guillemets `"` des secondes doivent être précédés d'un `\` dans le Terminal.
- `--hours` : sur combien d'heures calculer (120 h = 5 jours).
- Le départ du calcul est le départ de la course (dimanche 1er novembre, 12:02 UTC), ou maintenant si c'est plus
  tard.
- Si tu as déjà passé la porte de Fréhel, ajoute `--next-mark tete_anglais`.

La première fois dans un run météo, l'outil télécharge la météo (environ 100 fichiers, 26 Mo, **1 à 2 minutes**,
pour ne pas se faire bloquer par la NOAA). Les fois suivantes, elle est déjà sur le disque : 6 secondes au total.

## Ce que montre le résultat

Calcul fait le 31/10 avec le run GFS de 06h UTC, départ le 01/11 à 12:02 UTC depuis la ligne de départ Class40 :

| Heure | Position (format du jeu) | Cap | TWA | Vent | Voile | Vitesse |
|---|---|---|---|---|---|---|
| Départ | 48°43'48"N 001°54'00"W | 265° | +146° | 10,2 nd | LightGnk | 7,5 nd |
| +4 h | 48°52'53"N 002°46'14"W | 295° | +109° | 12,6 nd | Code0 | 11,3 nd |
| +8 h | 49°03'17"N 004°01'21"W | 280° | +136° | 16,6 nd | LightGnk | 13,5 nd |
| +12 h | 49°15'37"N 005°19'20"W | 290° | +135° | 16,2 nd | LightGnk | 13,5 nd |
| +16 h | 49°34'39"N 006°34'59"W | 300° | +136° | 16,0 nd | LightGnk | 13,3 nd |
| +24 h | 49°38'50"N 008°48'51"W | 305° | +146° | 16,1 nd | LightGnk | 12,0 nd |
| +48 h | 48°29'11"N 016°16'01"W | 240° | −129° | 18,8 nd | Code0 | 14,7 nd |

Comment lire une ligne : « à +8 h, le bateau devrait être à cette position ; à partir de là, mettre le cap au 280,
sous LightGnk ». TWA positif = vent qui vient de tribord.

En résumé : porte de Fréhel passée vers +2 h, route le long de la côte nord de la Bretagne en restant au nord du
rail d'Ouessant, puis vers l'ouest-nord-ouest pendant la première journée, avant de plonger vers le sud-ouest.
Au bout de 5 jours, il reste environ 2 110 milles jusqu'à l'arrivée.

L'outil écrit aussi deux fichiers dans `var/routes/` :
- un fichier `.json` avec la feuille de route complète (un point par heure le premier jour, puis toutes les 3 h) ;
- un fichier `.geojson` avec le tracé, qu'on pourra afficher sur la carte (et qu'on peut déjà ouvrir sur
  https://geojson.io pour le voir).

## Comment ça marche, en simple

1. L'outil part de ta position et essaie **72 caps** (tous les 5°).
2. Pour chaque cap, il lit le vent prévu à cet endroit, choisit **la voile la plus rapide** dans la polaire et
   avance d'une heure (de 3 h après les premières 24 h).
3. Il retire les trajets qui touchent la côte ou une zone interdite, et compte le **temps perdu** à chaque virement,
   empannage ou changement de voile (1 à 2 minutes selon le vent, d'après les réglages « winch pro » du jeu).
4. Il garde les meilleures positions atteintes (environ 700) et recommence depuis chacune.
5. À la fin, il prend le bateau le plus proche de l'arrivée et remonte son chemin : c'est la route.

## Limites à connaître

- **Un seul scénario météo** (le GFS du jeu). Pas encore d'options ni de probabilités : c'est l'étape 4.
- **Pénalités de manœuvre simplifiées** : une perte de temps fixe par manœuvre, calculée à partir de la polaire.
  Pas de gestion de l'énergie du skipper. Non vérifié dans le jeu.
- **Marques de Guadeloupe simplifiées** : les bouées sont des points de passage à moins de 2 milles, sans vérifier
  de quel côté on les laisse ; les Saintes sont seulement évitées comme de la terre.
- **Côte au 1/10 000 000 simplifiée à environ 400 m**, avec une grille de calcul d'environ 500 m : les petits
  cailloux et les détails des ports n'y sont pas. Le jeu utilise sa propre côte, que l'on ne connaît pas.
- Si tu es déjà en mer, il faut dire au calcul quelle est la prochaine marque (`--next-mark`).
- La météo couvre 0–60°N et 80°W–10°E : le calcul s'arrête au bord de cette zone.
