# Spécification du prompt d'extraction

## Référence actuelle

- Version : `v1.0`
- Langue : français
- Modèle utilisé pendant le stage : `qwen2.5:1.5b` via Ollama
- Implémentation : `Scripts/step9_llm_extract_database.py`
- Limite de texte : 2 500 caractères

## Contrat

Le modèle retourne uniquement un JSON valide, sans Markdown ni commentaire, avec les clés :

```text
titre, territoire, echelle, public_vise, nature_initiative,
description_generale, contexte, problematique, solution_envisagee, objectifs,
porteur_initiative, date, thematique, source_site
```

Le script regroupe les sous-champs descriptifs dans l'objet `description` conservé dans `LLM_Tagged_Database/`.

## Règles

1. Ne pas inventer d'information.
2. Déduire uniquement les informations fortement implicites.
3. Utiliser une chaîne ou liste vide lorsque l'information est absente ou ambiguë.
4. Préserver le `source_site` associé au dossier traité.

Toute modification du prompt exige une nouvelle version de ce document, l'archivage de la version précédente, une réévaluation sur le jeu de référence et une entrée dans `CHANGELOG.md`.
