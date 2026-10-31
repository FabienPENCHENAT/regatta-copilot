# Récupérer la polaire de ton bateau dans le jeu

**Est-ce nécessaire ?** Pas pour démarrer. Une copie publique de la polaire Class40 du jeu existe déjà
(mise à jour VR du 02/07/2024) et le routeur l'utilise. Ton export sert à **vérifier** qu'elle n'a pas changé.
Si tu le fais, ce sera la référence.

Méthode sans extension, avec les outils intégrés de Chrome (Edge et Firefox sont presque identiques).
Je n'ai pas pu la tester moi-même dans le jeu (il faut ton compte). Si un écran ne ressemble pas à ce qui est
décrit, dis-moi ce que tu vois.

## Étapes

1. Ouvre **Chrome sur ordinateur** (pas sur téléphone) et va sur le jeu Virtual Regatta Offshore. Connecte-toi,
   mais **n'entre pas encore** dans la course.
2. Ouvre les outils développeur : **Cmd + Option + I** sur Mac (F12 sur Windows). Un panneau s'ouvre.
3. Clique sur l'onglet **Network** (ou **Réseau**).
4. Coche **Preserve log** (ou **Conserver le journal**) en haut du panneau.
5. Dans le jeu, **entre dans la course** « Route du Rhum - Class40 ». Des dizaines de lignes défilent :
   c'est normal, ce sont les échanges entre le jeu et son serveur.
6. Dans le panneau Network, appuie sur **Cmd + F** (Ctrl + F sur Windows). Une barre « Search » apparaît à gauche.
   Tape : `globalSpeedRatio` puis Entrée. Ce mot n'existe que dans la polaire, ce qui la rend facile à trouver.
7. Un résultat s'affiche. Clique dessus : la requête correspondante s'ouvre à droite.
8. Clique sur l'onglet **Response** (ou **Réponse**) de cette requête. Tu vois un long texte qui commence par `{`.
9. Clic droit sur la requête dans la liste → **Copy** → **Copy response** (Copier la réponse).
10. Colle le tout dans un fichier texte nommé `polaire-class40.json` et envoie-le-moi, ou importe-le plus tard
    dans « Réglages » de l'outil.

## Comment savoir que c'est le bon texte

Il contient `"label":"mono/class40-2021"`, puis `"tws":[0,2,4,...]`, `"twa":[0,30,40,...]` et une liste
`"sail"` avec les noms `Jib`, `Spi`, `Staysail`, `LightJib`, `Code0`, `HeavyGnk`, `LightGnk`.

## Ce qu'il ne faut pas faire

- Ne partage pas d'autres requêtes : certaines contiennent ton jeton de connexion.
  La polaire, elle, ne contient aucune donnée personnelle.
- L'extension « VR Dashboard » citée par d'anciens tutoriels n'est plus nécessaire. D'après le Chrome Web Store,
  elle ne démarre plus avec les versions récentes de Chrome, et elle demande un accès « débogage » étendu au navigateur.
