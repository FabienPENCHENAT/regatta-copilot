# Le site calcule pour de vrai (31/10/2026)

**Lancer le site** : `./run.sh` dans le dossier du projet, puis ouvrir http://localhost:8000 (ou l'adresse
affichée pour le téléphone). La première fois, le script installe ce qu'il faut (quelques minutes).

## Ce qui a changé

- **« Calculer ma route » lance le vrai moteur** : météo GFS du jeu, polaire Class40, parcours officiel, zones
  interdites, et **uniquement tes voiles**. Le calcul prend environ 5 secondes. La première fois après une
  nouvelle prévision, la météo est téléchargée, ce qui prend environ 2 minutes.
- À l'ouverture, le site calcule tout seul depuis ta dernière position.
- **Réglages** :
  - une case par voile optionnelle (Génois léger, Spi léger, Trinquette, Spi lourd, Code 0) ;
  - dès que tu changes une case, la route est recalculée.

## Mise à jour du soir (31/10)

- **Le calcul ne tient compte que de tes voiles et de la vitesse propre à chaque bateau.** Plus de foils, de coque
  polie ni de winch pro : la route donne la direction, tu recalcules au fil de la course.
- **Les temps de manœuvre restent modifiables** dans les réglages. Ils sont pré-remplis avec les valeurs du jeu
  pour le bateau choisi et mémorisés par bateau, avec un bouton « Remettre les valeurs du jeu ». Mets 0 pour
  ignorer une manœuvre.
- **La feuille de route suit les ordres à donner** : une ligne par changement de cap (10° ou plus), de voile, ou
  par virement ou empannage, avec la durée. Par exemple : « Départ · 265° · Spi · 2 h », puis
  « +2 h · 290° · Spi · 1 h »…
- **Les 5 bateaux de la Route du Rhum calculent** : Class40, IMOCA, Ocean Fifty, Ultim et Vintage Multi.
  Changer de bateau recharge ses temps de manœuvre et relance le calcul.

## Ce qui n'est pas encore là

- **Les 31 scénarios** (étape 4). Pour l'instant, une seule option, « Route météo du jeu ». Les probabilités
  affichent « — » et la confiance « bientôt », plutôt que des chiffres inventés.
- **La route s'arrête à 5 jours.** « Course entière » montre ces 5 jours.
- **L'énergie du skipper**, qui allonge les manœuvres dans le jeu, n'est pas encore modélisée.
- **L'import de ta propre polaire** n'est pas encore branché.
