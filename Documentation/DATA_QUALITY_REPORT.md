# État de qualité de la base principale

## Contrôle du 31 août 2026

Commande exécutée :

```powershell
.\venv\Scripts\python.exe .\Scripts\validate_llm_database.py
```

Résultat sur `LLM_Tagged_Database/` :

| Statut | Nombre | Interprétation |
|---|---:|---|
| `valid` | 1 143 | Structure attendue et champs descriptifs présents. |

Le détail est disponible dans `outputs/quality_checks/llm_database_validation.csv`.

## Nettoyage réalisé

28 fichiers techniques qui n'étaient pas des fiches individuelles ont été déplacés, sans suppression, de `LLM_Tagged_Database/` vers `archive/llm_database_non_record_artifacts/`. Il s'agissait de fichiers agrégés ou de diagnostics tels que `all_*`, `errors_*`, `updated_*` et `new_or_updated_*`.

Ils ne doivent pas être réintégrés parmi les fiches sans traitement explicite.

## Corrections déterministes appliquées

Le script `Scripts/repair_metadata_from_provenance.py` a corrigé 11 incohérences à partir de valeurs déjà présentes dans les mêmes fichiers :

- 9 titres vides remplacés par `original_title`, après retrait d'une éventuelle extension de fichier ;
- 1 `public_vise` vide remplacé par `public non connu` ;
- 1 liste de porteurs transformée en une chaîne contenant les noms explicitement fournis.

Le journal détaillé est conservé dans `outputs/quality_checks/metadata_repairs.csv`. Aucun contenu source, aucune réponse LLM brute et aucun fichier de données n'a été supprimé.

## Contrôle à maintenir

Après toute nouvelle extraction ou normalisation, relancer le validateur et archiver son rapport. Une structure valide ne remplace pas la revue humaine de la pertinence factuelle des valeurs.
