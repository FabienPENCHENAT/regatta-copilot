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

## Version 2, après tes retours (31/10, après-midi)

Tu as gardé l'ordre des blocs, les options, la feuille de route et les réglages. Tu as demandé une vraie carte
marine avec le vent, un style plus marin, et un point de départ au bon endroit. Voici ce qui a changé.

- **Carte marine dessinée par l'outil**, sans service externe :
  - terre beige ;
  - plateau continental bleuté, avec les lignes de profondeur de 200 à 5 000 m ;
  - quadrillage des degrés avec les valeurs sur les bords ;
  - noms des mers en italique, comme sur les cartes du SHOM ;
  - cadre gradué noir et blanc, comme le bord d'une carte papier.
  En mode sombre, c'est une palette de nuit inspirée des écrans de navigation.
- **Le vent réel**, celui du modèle GFS que le jeu utilise, du run de 06h UTC aujourd'hui.
  - Il est affiché pour le départ de demain, puis à +4, 8, 12, 16, 24 et 48 h.
  - Tu peux choisir entre l'affichage animé (particules colorées selon la force du vent) et des barbules
    classiques. Le « ? » à côté des barbules explique comment les lire.
  - Toucher une heure, en bas de la carte ou dans la feuille de route, déplace le bateau à sa position prévue
    à ce moment-là.
- **Le parcours officiel** sur la carte :
  - ligne de départ Class40 ;
  - porte de Fréhel (bouées jaunes) ;
  - marques de Guadeloupe (rouge = à laisser à bâbord, vert = à tribord) ;
  - ligne d'arrivée ;
  - 22 zones interdites en magenta pointillé, comme les zones réglementées des cartes.
  Les coordonnées viennent directement des instructions de course officielles (avenants 1 et 2), enregistrées
  dans `races/route-du-rhum-2026.json`.
- **Départ au bon endroit** : l'exemple part maintenant de la ligne Class40 devant Saint-Malo
  (48°43,8' N, 1°54' W). Les routes passent par la porte de Fréhel, contournent le parc éolien de Saint-Brieuc et
  le rail d'Ouessant. Le cap, la voile et la vitesse affichés sont calculés avec le vrai vent et la vraie polaire
  Class40. Seules les options et leurs probabilités restent inventées.
- **Style marin** : bandeau bleu marine avec une rose des vents, titres soulignés de laiton, sous-titres en
  italique « carte marine ».

## Questions pour toi

- L'ordre des blocs te convient-il (réglages tout de suite après la saisie, puis la carte) ?
- Les horizons 4, 8, 12, 16, 24 et 48 h sont-ils les bons ?
- Les noms d'options (« Option Ouest », « Route directe », « Option Sud ») te parlent-ils ?
