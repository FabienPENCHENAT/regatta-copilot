# Les marques de Guadeloupe, les mises à jour automatiques et ta polaire (31/10/2026)

Trois nouveautés côté moteur. L'écran correspondant (choix de la prochaine marque, import de la polaire) est
branché en parallèle dans le site.

## 1. Le tour de la Guadeloupe

### Ce que disent les instructions de course

On fait le tour de la Guadeloupe **en la laissant à bâbord** (à gauche), donc dans le sens inverse des aiguilles
d'une montre : on longe la côte nord vers l'ouest, la côte ouest vers le sud, puis la côte sud vers l'est,
jusqu'à Pointe-à-Pitre.

| Marque | Côté | Ce que ça veut dire sur l'eau |
|---|---|---|
| Tête à l'Anglais (îlet au nord-ouest de Basse-Terre) | bâbord | tu passes **à l'ouest** de l'îlet en descendant vers le sud |
| Bouée de Basse-Terre | tribord | tu passes **entre la bouée et la côte** |
| Les Saintes | tribord | tu passes **au nord** des Saintes, par le canal des Saintes, vers l'est |
| Bouée d'atterrissage de Pointe-à-Pitre | bâbord | tu remontes vers le nord en laissant la bouée **à ta gauche** (tu passes à l'est de la bouée) |
| Arrivée | | ligne à 16°12'N, franchie vers le nord |

### Comment le routeur le vérifie

Avant, ces marques étaient de simples points à toucher à 2 milles près : le routeur ne vérifiait pas le côté.
Maintenant, chaque marque est une **ligne imaginaire** qui part de la marque vers la terre ou le large, et qu'il
faut traverser dans un sens précis. Exemple : de l'îlet Tête à l'Anglais, une ligne part vers l'ouest ; la route
doit la traverser en descendant. Passer à l'est de l'îlet ne compte pas.

Ces lignes **ne viennent pas du jeu ni des instructions** : je les ai construites à partir des côtés imposés
(statut « dérivé » dans le fichier de course). Le trait de côte utilisé est assez grossier (précision d'environ
500 m). Près de la bouée de Basse-Terre, la zone interdite du « stade nautique » coupe le passage : il reste de
l'eau libre de part et d'autre, et les routes calculées passent bien. **Compare avec la carte du jeu** : Virtual
Regatta ne publie pas ses lignes.

Autre correction : une route ne pouvait jamais « arriver », parce que la terre et la zone des spectateurs, juste
derrière la ligne d'arrivée, bloquaient le dernier bout de trajet. La route s'arrête maintenant sur la ligne.

### Choisir la prochaine marque

Le routeur devine tout seul quand la porte de Fréhel est passée (tu es à plus de 2 milles à l'ouest). Mais
autour de la Guadeloupe, **ta position seule ne suffit pas** à savoir si tu as déjà contourné une marque : en
automatique, il visera toujours Tête à l'Anglais.

Donc, quand tu arrives en Guadeloupe :
- laisse **« Automatique »** tant que tu n'as pas passé Tête à l'Anglais ;
- ensuite, choisis la **prochaine marque** dans la liste : « Bouée de Basse-Terre », puis « Les Saintes », puis
  « Bouée de Pointe-à-Pitre », puis « Arrivée ».

Le résultat indique toujours quelle marque a été visée et si c'était automatique ou ton choix.

Essai réel (prévision de 06 h le 31/10, Class40, Jib et Spi seulement) depuis 17°N 60°W : la route fait le tour
complet dans le bon sens et arrive en environ 17 heures (183 milles).

## 2. Les mises à jour se font toutes seules

Avant, quand une nouvelle prévision GFS sortait, le premier calcul la téléchargeait et te faisait attendre
environ 2 minutes.

Maintenant, tant que le site tourne (`./run.sh`), **toutes les 10 minutes** il vérifie en arrière-plan :
1. s'il y a une nouvelle prévision GFS (celle du jeu), il la télécharge ;
2. s'il y a une nouvelle série de 31 scénarios (GEFS), il la télécharge (environ 15 minutes) ;
3. dès qu'une nouvelle prévision est arrivée, il **recalcule ta dernière demande** (même course, même bateau,
   même position, mêmes réglages) et garde le résultat.

Résultat : quand tu rouvres le site, la route s'affiche **tout de suite**. Pendant un téléchargement, tes calculs
utilisent la prévision précédente, déjà sur l'ordinateur ; le résultat est alors refait 30 minutes plus tard au
plus. Pendant la course, comme l'heure de départ du calcul avance, ta dernière demande est aussi recalculée toutes
les 30 minutes environ pendant 6 heures après ta dernière visite.

Il faut que l'ordinateur reste allumé et le site lancé. La dernière demande est gardée dans
`var/last_request.json`, et les messages du type « GFS run … » ou « pre-computed the last route request »
s'affichent dans le terminal.

## 3. Ta propre polaire

Le site utilise par défaut une copie publique de la polaire du jeu. Tu peux importer **la tienne**, copiée dans
le jeu : c'est alors elle qui sert pour tous les calculs de ce bateau sur cette course (la route du jeu et les
31 scénarios).

1. Copie la réponse du jeu qui contient la polaire, en suivant
   [extraire-polaire-vr.md](extraire-polaire-vr.md) (étapes 1 à 9 : outils développeur de Chrome, onglet
   Network, recherche `globalSpeedRatio`, clic droit → Copy response).
2. Dans le site, ouvre **Réglages**, partie polaire, et **colle** le texte (ou importe le fichier).
3. Le site vérifie qu'il y a bien 7 voiles, des tableaux de vitesse complets et les temps de manœuvre. Sinon, il
   te dit ce qui manque, et rien n'est changé.
4. C'est fait : les réglages indiquent « ta polaire » avec la date d'import, et la route est recalculée.

Pas besoin de nettoyer le texte copié : le site va chercher la polaire à l'intérieur, et **ne garde que la
polaire** (pas tes informations de connexion qui pourraient se trouver autour). Elle est enregistrée dans
`var/polars/` sur ton ordinateur.

Pour revenir à la polaire publique : bouton **« Revenir à la polaire publique »** dans les réglages.
