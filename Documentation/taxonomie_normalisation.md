# Taxonomie de normalisation des métadonnées

Ce document décrit la taxonomie utilisée par `Scripts/normaliser_taxonomie.py`.
Elle sert à faciliter les filtres, statistiques et comparaisons du projet
Index_Insight. Elle ne remplace pas les valeurs produites par le LLM : les
champs `thematique` et `nature_initiative` restent inchangés dans les fichiers
JSON.

## Principe

Le script ajoute les champs suivants :

- `thematique_normalisee` : liste de thèmes contrôlés ;
- `nature_initiative_normalisee` : nature contrôlée unique ;
- `version_taxonomie` : version de la taxonomie appliquée.

Lorsqu'une valeur est ambiguë ou absente de la taxonomie, le script utilise
`autre / à revoir` au lieu de produire une correspondance arbitraire. Le fichier
`outputs_graphs/normalisation_taxonomie/valeurs_a_revoir.csv` doit être relu
après chaque exécution afin d'améliorer explicitement les correspondances.

## Thèmes contrôlés

1. autonomie et avancée en âge ;
2. santé et prévention ;
3. aidants, handicap et vulnérabilités ;
4. lien social et lutte contre l'isolement ;
5. intergénérationnel ;
6. mobilité et accessibilité ;
7. habitat et logement ;
8. numérique et accès à l'information ;
9. participation citoyenne et gouvernance ;
10. culture et loisirs ;
11. activité physique et sport ;
12. espaces publics et aménagement ;
13. services et accompagnement ;
14. politiques publiques et recherche ;
15. environnement et développement durable ;
16. autre / à revoir.

Une initiative peut recevoir plusieurs thèmes normalisés lorsque son libellé
brut indique clairement plusieurs dimensions, par exemple `mobilité et
isolation`.

## Natures d'initiative contrôlées

1. atelier ;
2. formation ;
3. sensibilisation ;
4. enquête ou étude ;
5. rapport ou publication ;
6. plaidoyer ;
7. outil numérique ;
8. événement ;
9. accompagnement ;
10. dispositif ou programme ;
11. offre de service ;
12. groupe de parole ;
13. consultation citoyenne ;
14. lieu ou espace dédié ;
15. projet d'aménagement ;
16. autre / à revoir ;
17. non renseigné.

## Exécution

Exécuter d'abord sans modifier les données :

```powershell
py .\Scripts\normaliser_taxonomie.py --dry-run
```

Lire `valeurs_a_revoir.csv`. Lorsque les correspondances conviennent, appliquer
la normalisation :

```powershell
py .\Scripts\normaliser_taxonomie.py --apply
```

Les graphiques et tableaux doivent ensuite utiliser les champs normalisés, tout
en conservant les valeurs brutes pour l'audit et la correction.
