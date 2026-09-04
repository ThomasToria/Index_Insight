# Scripts

## Familles de scripts

| Famille | Exemples | Rôle |
|---|---|---|
| Collecte | `cnav_scrap.py`, `fdf_scrap.py`, `vada_scrap.py`, `hcfea_scrap.py` | Collecter les sources. |
| Préparation | `Docx_to_txt.py`, `filename_cleaner.py`, `step1_clean_fiches_actions.py` | Produire des textes propres. |
| Baseline historique | `step2_` à `step8_` | Pipeline rule-based, conservé pour comparaison. |
| LLM | `step9_llm_extract_database.py` | Extraire des JSON locaux avec Ollama. |
| Normalisation | `normaliser_taxonomie.py`, `ajouter_provenance.py` | Harmoniser catégories et provenance. |
| Évaluation | `create_llm_evaluation_sample.py`, `score_llm_annotations.py`, `score_rule_based_baseline.py` | Créer et scorer le jeu de référence. |
| Qualité | `validate_llm_database.py` | Vérifier la structure de la base principale sans la modifier. |
| Réparation contrôlée | `repair_metadata_from_provenance.py` | Réparer des champs vides uniquement à partir de métadonnées existantes. |
| Exports | `generate_graphs.py`, `generate_thesis_figures.py` | Produire graphiques et fichiers de travail. |

## Règle de sécurité

Avant d'exécuter un script modifiant `LLM_Tagged_Database/`, créer une copie datée ou un commit. Avant une normalisation, lancer systématiquement le mode `--dry-run`.
