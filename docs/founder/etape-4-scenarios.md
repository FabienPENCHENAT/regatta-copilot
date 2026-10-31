# Étape 4 : plusieurs routes et leurs probabilités (31/10/2026)

## L'idée en deux phrases

La météo à 2 ou 3 jours n'est jamais sûre. Au lieu d'une seule prévision, la NOAA publie toutes les 6 heures
**31 versions légèrement différentes** de la même prévision (l'« ensemble » GEFS). Le routeur calcule ta route
sur chacune des 31, puis regarde **où elles vont** : si elles partent toutes du même côté, il n'y a qu'une
option ; si elles se séparent, chaque groupe devient une option.

## Comment lire les options

- **Le nom** dit de quel côté de la route « moyenne » (le milieu de toutes les routes) passe l'option,
  surtout à +24 h et +48 h :
  - « Consensus » : les 31 routes vont au même endroit, il n'y a qu'une option ;
  - « Directe » : l'option la plus au milieu du paquet ;
  - « Nord » / « Sud » : l'option passe à droite / à gauche de la route moyenne (vers l'ouest, la droite
    c'est le nord) ;
  - « Ouest » (ou « Est ») : une deuxième option du même côté, moins écartée que la première.
- **Le type** : « la plus courte » est l'option la plus proche de la ligne droite vers la prochaine marque ;
  les autres sont des options de **placement** (aller chercher un vent meilleur plus loin).
- **La probabilité**, c'est la part des 31 prévisions dont la meilleure route passe par cette option.
  Exemple : 20 sur 31 = 65 %. Ce n'est pas une garantie : si les 31 prévisions se trompent toutes dans le même
  sens, l'option à 65 % peut perdre.
- **L'option recommandée** est la plus probable.
- **« Route du jeu »** marque l'option où passe la route calculée sur la météo du jeu (GFS, celle que Virtual
  Regatta utilise vraiment). Elle ne compte pas dans les probabilités.
- **La confiance** de chaque ligne de la feuille de route : la part des prévisions de l'option qui passent dans
  le cercle autour du point visé à cette heure-là (le cercle grandit avec le temps : 7 milles à +4 h,
  46 milles à +48 h). Haute = les prévisions sont d'accord.
- **Le retard estimé** (« +3 h ») compare l'arrivée de chaque option à la meilleure. C'est une approximation :
  le calcul s'arrête à 5 jours, le reste est estimé avec la vitesse moyenne de l'option.
- Sur la carte, chaque fine ligne est la route d'une des 31 prévisions, de la couleur de son option.

## Le premier téléchargement est long

- Les 31 prévisions représentent environ **1 400 petits fichiers** (≈ 90 Mo) par prévision. Le serveur de la
  NOAA bannit ceux qui demandent trop vite, donc on télécharge doucement : **environ 15 minutes**
  (mesuré le 31/10 : 1 426 fichiers, 93 Mo, 14 min 48 s).
- Pendant ce temps, le site **ne bloque pas** : il donne la route du jeu (une seule option, comme avant) et
  indique que les scénarios se téléchargent. Quand c'est prêt, un nouveau calcul affiche les options.
- C'est fait **une fois par prévision** (toutes les 6 heures). Ensuite, un calcul prend **environ 50 secondes** sur ton Mac (31 routes + celle du jeu).
- Pour préparer à l'avance, dans le dossier du projet :
  `.venv/bin/python -m sailrouter ensemble-download`

## Premier résultat réel (départ Class40, Jib + Spi seulement)

Prévision du 31/10 à 06 h UTC, départ le 1er novembre à 12 h 02 UTC, 120 heures calculées :

| Option | Probabilité | Route du jeu | Tout de suite | À +24 h | À +48 h | Retard estimé |
|---|---|---|---|---|---|---|
| Directe (recommandée) | 10/31 = 32 % | | cap 265°, Spi | 49°32' N 8°16' W, cap 295°, Spi | 48°10' N 15°12' W, cap 245°, Spi, 20 nds | +9 h |
| Sud | 8/31 = 26 % | oui | cap 265°, Spi | 48°32' N 8°16' W, cap 295°, Spi | 47°43' N 15°23' W, cap 240°, Spi, 20 nds | la meilleure |
| Ouest (la plus courte) | 7/31 = 23 % | | cap 270°, Spi | 49°15' N 8°13' W, cap 235°, Spi | 46°45' N 15°43' W, cap 250°, Spi, 22 nds | +12 h |
| Nord | 6/31 = 19 % | | cap 290°, Spi | 50°02' N 8°00' W, cap 305°, Spi | 48°37' N 15°42' W, cap 255°, Spi, 19 nds | +15 h |

Comment le lire :
- Les 4 options partent toutes vers l'ouest sous Spi (avec un passage au Jib vers +4 h pour les deux
  premières) : **la décision des premières heures est la même**, ce qui compte c'est où tu sors de la Manche.
- Aucune option ne domine (32 % au plus) : les prévisions ne sont pas d'accord sur la suite, c'est normal à
  2 jours. Recalcule à chaque nouvelle prévision (toutes les 6 h).
- La route du jeu (GFS) est dans l'option « Sud », qui est aussi celle qui arrive le plus tôt selon
  l'estimation.
- « Nord » a une confiance faible (33 % à +8 h) : ses 6 prévisions sont elles-mêmes dispersées.

## Limites à connaître

- La météo de l'ensemble est **moins fine** (0,5°, toutes les 3 heures) que celle du jeu (0,25°, toutes les
  heures). Elle sert à savoir **de quel côté** aller, pas au mille près.
- Les routes s'arrêtent à **5 jours** ; au-delà, rien n'est calculé.
- Les groupes sont faits avec une règle simple (deux routes à moins d'environ 70 milles à +48 h sont dans la
  même option). Une prévision isolée rejoint le groupe le plus proche plutôt que de créer une option à 3 %.
- Au plus **4 options**.
- Le calcul avec les 31 scénarios prend environ 50 secondes : la page attend pendant ce temps.
- Rien n'a été vérifié dans le jeu lui-même.


## Mise à jour : résultats gardés jusqu'à la prochaine météo (31/10)

Entre deux prévisions, rien ne change. Le site garde donc chaque résultat calculé. Si tu rouvres le site avec la
même position, le même bateau, les mêmes voiles et les mêmes temps de manœuvre, la réponse est immédiate
(0,02 s au lieu de 50 s). Dès qu'une nouvelle prévision est disponible, ou que tu changes de position ou de
réglage, le site recalcule une fois, puis garde ce nouveau résultat.

Les cartes d'options n'affichent plus le « +X h à l'arrivée », qui n'était pas comparable d'une option à l'autre.
Elles indiquent le nombre de scénarios qui vont dans ce sens : c'est sur ce regroupement que repose le conseil.
