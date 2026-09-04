# Guide de reprise — Index_Insight

## Avant toute modification

`LLM_Tagged_Database/` est la base principale. Ne pas l'écraser sans copie datée, export ou commit permettant de revenir à l'état précédent.

Le mémoire s'appuie sur 1 153 documents, tandis que la base actuellement transmise contient 1 143 fiches JSON après archivage de 28 agrégats techniques. Avant toute analyse, noter la date de l'instantané, le nombre de fichiers et les sources incluses.

## Ce qui fonctionne

- Collecte et préparation de plusieurs sources françaises ;
- extraction locale avec JSON contraint ;
- normalisation déterministe des thèmes et natures d'initiative ;
- exports, graphiques et prototype ;
- évaluation humaine initiale sur 60 documents ;
- comparaison LLM / baseline rule-based.

## Ordre de reprise recommandé

1. Installer l'environnement et vérifier Ollama.
2. Lire `PIPELINE.md` et `DATA_DICTIONARY.md`.
3. Lancer `py .\Scripts\validate_llm_database.py` et archiver le rapport produit. Au 31 août 2026, les 1 143 fiches de la base principale sont conformes au schéma attendu.
4. Traiter chaque nouvelle source dans un dossier isolé avant intégration.
5. Exécuter la normalisation en `--dry-run`, lire les valeurs ambiguës, puis appliquer après validation.
6. Mettre à jour exports, `CHANGELOG.md` et documentation de provenance.

## Vigilances

- Les structures documentaires changent selon les sources.
- Une valeur JSON non vide n'est pas automatiquement factuelle.
- Dates, territoires et porteurs peuvent être ambigus.
- Toute nouvelle collecte doit renseigner `source_url`, `original_title`, `collection_date` et `source_site`.
- `Final_Tagged_Database/` est une baseline ; ce n'est pas la base de production.

## Priorités

1. Compléter la provenance des nouvelles ressources.
2. Ajouter un second annotateur et calculer l'accord inter-annotateur.
3. Réévaluer après toute modification du modèle, prompt ou taxonomie.
4. Réduire le déséquilibre entre sources et documenter la politique de collecte.
5. Détecter les doublons.
6. Réviser la taxonomie avec des professionnels.
7. Co-construire toute extension internationale, car les termes, catégories et contextes institutionnels varient selon les pays.

Le projet privilégie une extraction locale, contrainte, traçable et révisable : l'objectif est de créer un index vérifiable, pas d'automatiser sans contrôle humain.
