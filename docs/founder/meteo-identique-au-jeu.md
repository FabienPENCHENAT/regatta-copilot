# Le même vent que dans le jeu (3 novembre 2026)

## Ce que tu as vu

À 47°13'N 23°38'W, le jeu donnait **Spi léger, 11,3 nœuds, avec 8,6 nœuds de vent**. Le site annonçait, sur
l'option « Météo du jeu », **Code 0, 20,5 nœuds, avec 14 nœuds de vent**.

## Les deux causes

1. **Chaque option affichait la route d'un des 31 scénarios**, même celle marquée « Météo du jeu ». Le
   scénario choisi pour la représenter avait 14 nœuds à cet endroit, alors que la vraie prévision du jeu en
   avait environ 9.
2. **Le jeu ne passe pas d'une prévision à l'autre d'un coup.** Pendant les premières heures, il mélange
   l'ancienne et la nouvelle : ce sont les jauges bleue (ancienne) et verte (nouvelle) du journal de bord. Le
   site, lui, prenait la nouvelle d'un coup. Règle trouvée dans le guide d'eSail4VR, un routeur branché sur le
   jeu : une prévision ne sert qu'à partir de 9 h après son heure de calcul. Par exemple, le run de 06Z ne sert
   qu'à partir de 15 h UTC, et entre 12 h et 15 h le jeu mélange 00Z et 06Z.

## Ce qui a changé

- L'option « Météo du jeu » affiche maintenant **la vraie route du jeu**.
- Les autres options sont **rejouées dans la météo du jeu** : cap, voile, vitesse et vent sont ceux que le
  jeu te donnera si tu les suis. Les 31 scénarios servent toujours à trouver les options et leurs probabilités.
- La météo du site **mélange les deux prévisions comme le jeu**, pour le calcul, les options et la carte.

Résultat sur ta position : le site donne Spi léger, 11,2 nœuds, avec 8,8 nœuds de vent, au cap 241° (le jeu :
11,3 nœuds au cap 237°).

## Ce qui reste à vérifier

Quand la NOAA publie une prévision en retard, on ne sait pas encore si le jeu garde la même règle des 9 h. Si
un jour la météo du jeu et celle du site ne collent pas juste après un retard, envoie une capture du journal
de bord (bulletin actuel, prochain bulletin et leurs jauges).

Détails techniques : décisions D63 et D64 dans [../ai/decisions.md](../ai/decisions.md).
