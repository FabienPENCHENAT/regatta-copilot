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
  - foils, coque polie et winch pro ;
  - dès que tu changes une case, la route est recalculée.
- **Temps de manœuvre** : ils ne se saisissent plus. Ils sont lus dans la polaire du jeu, par exemple « virement
  de 3 à 5 min à 50 % de vitesse » sans winch pro.

## Ce qui n'est pas encore là

- **Les 31 scénarios** (étape 4). Pour l'instant, une seule option, « Route météo du jeu ». Les probabilités
  affichent « — » et la confiance « bientôt », plutôt que des chiffres inventés.
- **La route s'arrête à 5 jours.** « Course entière » montre ces 5 jours.
- **L'énergie du skipper**, qui allonge les manœuvres dans le jeu, n'est pas encore modélisée.
- **L'import de ta propre polaire** n'est pas encore branché.
