# Journal des changements

## État de transmission — 31 août 2026

- `LLM_Tagged_Database/` est la base principale.
- Le mémoire repose sur un instantané antérieur de 1 153 documents. Après archivage non destructif de 28 agrégats et rapports techniques, la base principale contient 1 143 fiches JSON.
- Après 11 corrections déterministes issues de la provenance existante, le validateur confirme 1 143 fiches conformes ; voir `Documentation/DATA_QUALITY_REPORT.md`.
- Extraction locale avec Ollama et `qwen2.5:1.5b`.
- Normalisation par `Scripts/normaliser_taxonomie.py`, taxonomie `v1.0`.
- Évaluation humaine stratifiée de 60 documents et comparaison LLM / baseline disponibles dans `Evaluation/`.

## Limites ouvertes

- Déséquilibre entre les sources, notamment la surreprésentation de RFVAA dans l'instantané du mémoire.
- Ambiguïtés possibles pour les dates, territoires et porteurs.
- `collection_date` reste incomplètement renseigné.
- Une seconde annotation est nécessaire pour mesurer l'accord inter-annotateur.

## Règle de versionnement

Pour chaque nouvelle exécution complète, noter : date, nombre de fichiers, sources incluses, modèle, version du prompt, version de la taxonomie et emplacement des exports.
