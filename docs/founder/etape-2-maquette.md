# Étape 2 : maquette de l'écran (31/10/2026)

Maquette en ligne (privée, à ouvrir aussi sur téléphone) : https://claude.ai/artifact/WYFjEWSudrSqdcGTxKLhqh

En local : `python3 -m http.server 8000 -d frontend`, puis ouvrir http://localhost:8000.

**Les chiffres sont un exemple fabriqué**, pas un vrai calcul : un Class40 au sud-ouest de la Bretagne,
le 2 novembre.

## Ce que montre l'écran, de haut en bas

1. **Ma course** : course, bateau, position. Tu peux coller la position du jeu (`47°30'00"N 006°45'00"W`) ou des
   degrés décimaux (`47.5, -6.75`). La position comprise s'affiche tout de suite, et le point apparaît sur la carte.
2. **À régler maintenant** : cap, voile, angle au vent (TWA), force du vent (TWS) et vitesse pour l'option
   conseillée, avec une phrase de conseil.
3. **Carte** :
   - en trait épais, l'option choisie ;
   - en traits fins, les 31 scénarios, colorés selon l'option qu'ils suivent ;
   - en cercles, les zones à viser à 4, 8, 12, 16, 24 et 48 h : vert = fiable, orange = incertain, rouge = très
     incertain.
4. **Les options possibles** : par exemple « Option Ouest : se placer pour la météo dans 2 jours, 55 % de
   chances d'être la meilleure » ou « Route directe : la plus courte, 26 % ». Chaque option indique aussi si
   c'est la route de la météo du jeu. Toucher une option met à jour la carte et la feuille de route.
5. **Feuille de route** : pour l'option choisie, à 4, 8, 12, 16, 24 et 48 h, la position à viser (au format
   du jeu), le cap, la voile, le vent, la vitesse et la confiance. Sur téléphone, chaque étape devient une carte.
6. **Réglages** (fermés par défaut) : options du bateau, temps perdu par manœuvre, polaire (import du JSON du jeu).

Chaque terme technique (Cap, TWA, TWS, Confiance, probabilité) a un bouton « ? » qui l'explique.

## Ce que veut dire la probabilité

Pour chaque scénario météo, le routeur calcule la meilleure route. Ensuite, il regroupe les routes qui vont au même
endroit. Exemple : si 17 des 31 meilleures routes passent par l'ouest, l'option Ouest a 17/31 = 55 % de chances
d'être la meilleure. La route GFS du jeu est calculée en plus, mais n'entre pas dans ce compte.

## Questions pour toi

- L'ordre des blocs te convient-il (réglages tout de suite après la saisie, puis la carte) ?
- Les horizons 4, 8, 12, 16, 24 et 48 h sont-ils les bons ?
- Les noms d'options (« Option Ouest », « Route directe », « Option Sud ») te parlent-ils ?
