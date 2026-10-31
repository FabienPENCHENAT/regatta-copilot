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

## Version 3 : identité « océan » et tracé complet (31/10)

- **Tracé idéal jusqu'à l'arrivée** : surligné en jaune avec un pointillé, de Saint-Malo jusqu'à la ligne d'arrivée,
  tour de la Guadeloupe compris. Il est purement visuel et n'influence aucun calcul. Le bouton « Course entière »
  sous la carte affiche tout le parcours, « 48 h » revient sur les deux prochains jours.
- **Identité visuelle** : bandeau « océan » avec des vagues à crêtes enroulées et des embruns qui dérivent
  doucement, et une touche manga légère (contours à l'encre, ombres franches comme des cases de BD, lignes de
  vitesse et bulle de conseil dans « À régler maintenant », étiquettes « autocollant »). Le fond de page est une
  carte marine ancienne : lignes de rhumb, roses des vents, isobathes en pointillés, sondes en italique. Couleurs :
  bleu océan, lagon turquoise, corail, soleil, sable. La nuit, c'est l'océan profond.
- Le tracé recommandé est désormais corail, comme le bouton principal et le bateau.

## Version 4 : la carte au centre (31/10)

Inspirée de ta capture « tableau de bord » :
- **La carte occupe tout l'écran.** Les panneaux flottent dessus, en verre dépoli. Mer bleu-gris, terre claire,
  noms des mers en italique.
- **Barre d'icônes à gauche** (en bas sur téléphone) : chaque icône affiche ou masque un panneau pour libérer la
  carte. La roue dentée ouvre les réglages, en fenêtre.
- **En haut à gauche** : « Bonne route, skipper » et la saisie (course, bateau, position).
- **En haut à droite** : les contrôles de la carte (48 h ou course entière, heure, vent animé ou barbules), la
  légende repliable, puis la feuille de route en liste compacte avec une barre de confiance colorée par étape.
- **En bas** : « À régler maintenant » en tuiles (cap en bleu, voile en vert, vent et vitesse en blanc) et les
  options avec un anneau de probabilité.
- **Sur la carte** : les zones à viser deviennent des points lumineux qui pulsent doucement, en vert, orange ou
  rouge selon la confiance.
- Sur téléphone, la carte occupe la moitié haute et les panneaux défilent par-dessus.
- Le style « manga » et le fond portulan de la version 3 ont été retirés.

## Version 5 : corrections (31/10)

- « À régler maintenant » suit l'option sélectionnée. Dans l'exemple, les trois options ont le même réglage au
  départ, car elles passent toutes par Fréhel et Ouessant avant de se séparer vers +16 h.
- Réglages refaits : une seule colonne, des lignes « Virement [3] min », un vrai bouton d'import de polaire.
- La roue dentée des réglages ressemble à une roue dentée. Un bouton lune/soleil bascule le thème clair ou sombre,
  et le choix est mémorisé.
- Logo : un foc, version minimaliste.
- **Lancer le site en local** : `./run.sh` à la racine du projet, puis ouvrir http://localhost:8000. Le script
  affiche aussi l'adresse à ouvrir sur ton téléphone (même Wi-Fi).

## Version 6 : harmonisation (31/10, soir)

- **Adresse du site : http://localhost:8000** (lancé par `./run.sh`). L'aperçu sur claude.ai n'est plus mis à jour.
- **Couleurs** : tout part du bloc « À régler maintenant ». Les options sont en bleu, menthe et violet. La confiance
  ne s'affiche plus en feu tricolore, mais par l'intensité du bleu (barres) ou du blanc (points sur la carte).
- **Scintillement corrigé** : il venait de l'effet verre au-dessus des particules de vent animées. Les panneaux
  sont désormais opaques.
- **Écriture** : police Geist, plus moderne. La phrase « Ta route au large… » est supprimée.
- **Options** : une ligne compacte chacune. Le détail apparaît au survol.
- **Tuiles** : chiffre en grand, unité en petit. La vitesse a sa propre tuile foncée.
- **Logo** : grand-voile et foc à facettes. **Réglages** : nouvelle icône en curseurs.
- **Nouvelle page « Comment ça marche »** (icône « i ») : d'où viennent les données, quand la météo se met à jour,
  comment une route est calculée, comment naissent les options et leurs probabilités, et les limites de l'outil.

## Version 7 : instruments de bord (31/10, soir)

- La barre de gauche ne garde que l'essentiel : thème, réglages, « Comment ça marche », langue. Les boutons qui
  masquaient les panneaux ont disparu.
- Carte : vues « 24 h », « 48 h » et « Course entière ».
- « À régler maintenant » devient un tableau d'instruments :
  - **compas** : le bateau pointe vers son cap, la flèche verte montre d'où vient le vent ;
  - **voiles** : les 7 voiles du Class40 avec leur silhouette, celle à envoyer en grand ;
  - **vent réel** : une jauge aux couleurs du vent de la carte, avec la force Beaufort (« Force 3 · petite brise ») ;
  - **vitesse** : un cadran de 0 à 20 nœuds.
- Sur ordinateur, les options s'empilent à droite du tableau d'instruments et la feuille de route prend toute
  la hauteur à droite.

## Version 8 : panneaux repliables (31/10, soir)

- Après « Calculer ma route », le bloc « Ma course » se replie en une ligne (course, bateau, position) avec un
  bouton « Modifier ».
- « À régler maintenant » se range vers le bas avec la petite flèche en haut à droite. Il n'en reste que le titre,
  et un clic dessus le fait remonter.
- Toute la colonne de droite (contrôles de la carte, légende, feuille de route) se range vers la droite avec la
  flèche sur son bord gauche. Une fine bande reste visible ; un clic dessus la ramène.
- Les options restent toujours visibles.

## Version 9 : bloc du bas repliable, nouveau bloc « course », légende allégée (31/10)

- Tout le bloc du bas (« À régler maintenant » + options) se range vers le bas avec la flèche ronde, comme la
  colonne de droite. Les deux rangés, on voit presque toute la carte.
- Le bloc « Route du Rhum 2026 » est redessiné : nom de la course en titre, ligne Saint-Malo → Pointe-à-Pitre avec
  la distance officielle (3 542 milles), pastille « Départ dans 22 h » (puis « En course depuis… »), bateaux en
  pastilles, champ de position avec repère et coche verte, bouton bleu « Calculer ma route ».
- La légende ne garde que les symboles de la carte et une ligne toujours visible : « Mise à jour des données vers
  17:30 · dans 2 h 02 », à ton heure locale.

## Version 10 : tes voiles et tes options (31/10)

- Dans « Réglages », coche les options que tu possèdes dans le jeu. Par défaut : foils seulement, comme ton bateau.
  Le Jib et le Spi sont toujours à bord.
- Le calcul n'utilise que tes voiles. Sur la météo de ce matin, ça change vraiment la route : avec ton bateau, le
  routeur passe plus au nord le premier jour et il reste 21 milles de plus à faire au bout de 5 jours.
- Les noms des voiles sont ceux du jeu : Jib, Spi, Trinquette, Génois léger, Code 0, Spi lourd, Spi léger. Celles que
  tu n'as pas sont barrées dans « À régler maintenant ».
- Tous les bateaux de la Route du Rhum ont les mêmes 7 voiles. Seul l'effet des options change selon le bateau : par
  exemple, les foils donnent +8 % en IMOCA contre +4 % sur les autres. Le calcul en tient compte via la polaire de
  chaque bateau.

## Questions pour toi

- L'ordre des blocs te convient-il (réglages tout de suite après la saisie, puis la carte) ?
- Les horizons 4, 8, 12, 16, 24 et 48 h sont-ils les bons ?
- Les noms d'options (« Option Ouest », « Route directe », « Option Sud ») te parlent-ils ?
