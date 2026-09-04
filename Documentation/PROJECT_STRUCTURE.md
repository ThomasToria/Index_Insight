# Structure du projet

| Dossier | Rôle | Statut |
|---|---|---|
| `LLM_Tagged_Database/` | JSON extraits par le LLM, normalisés et enrichis de provenance. | Base principale |
| `Cleaned_Database/` | Textes nettoyés fournis au modèle. | À conserver |
| `Database/` | Contenus collectés avant nettoyage. | À conserver |
| `Candidates_Database/`, `Segmented_Database/`, `Sectioned_Database/`, `Entities_Database/`, `Scored_Database/` | Étapes intermédiaires de la baseline historique. | Audit |
| `Final_Tagged_Database/` | Sortie de la baseline rule-based. | Comparaison uniquement |
| `LLM_Tagged_Database_backup_avant_harmonisation/` | Sauvegarde avant harmonisation. | Archive à préserver |
| `Evaluation/` | Échantillons, annotations, résultats et scripts d'évaluation. | Référence d'évaluation |
| `outputs/`, `outputs_graphs/`, `Figures/` | Exports et figures régénérables. | Sorties |
| `Scripts/` | Collecte, préparation, extraction, normalisation et évaluation. | Code |
| `Documentation/` | Documentation de reprise. | Documentation |
| `prototype-siage/` | Prototype d'interface consommant les données structurées. | Interface |

## À ne pas versionner comme des données

- `venv/` : environnement local ;
- `tmp/`, `temp/`, `.xlsx_work/` : travail régénérable ;
- `Scripts/__pycache__/` : cache Python.

Ne supprimer ni données brutes, ni réponses LLM brutes, ni sauvegardes sans vérification : ces éléments permettent l'audit et la correction.
