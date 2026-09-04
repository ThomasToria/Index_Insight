# Index_Insight

Index_Insight construit un corpus documentaire français sur les réponses territoriales au vieillissement, puis le transforme en fiches JSON traçables. Le projet a été développé dans le cadre d'un stage de Master 2 NLP avec la Chaire internationale SIAGE.

## Base principale

La base de référence est **`LLM_Tagged_Database/`**. Chaque fichier JSON correspond à une ressource et contient les métadonnées extraites par le LLM local, les champs de normalisation et les informations de provenance disponibles.

`Final_Tagged_Database/` est l'ancienne baseline rule-based : elle doit uniquement servir aux comparaisons expérimentales.

## Installation

```powershell
py -m venv venv
.\\venv\\Scripts\\Activate.ps1
py -m pip install -r requirements.txt
ollama pull qwen2.5:1.5b
```

Consulter ensuite [le guide de reprise](Documentation/HANDOVER.md) avant toute exécution.

## Documentation

- [Guide de reprise](Documentation/HANDOVER.md)
- [Architecture du pipeline](Documentation/PIPELINE.md)
- [Dictionnaire de données](Documentation/DATA_DICTIONARY.md)
- [Évaluation](Documentation/EVALUATION.md)
- [Structure du projet](Documentation/PROJECT_STRUCTURE.md)
- [Spécification du prompt](Documentation/PROMPT_SPECIFICATION.md)
- [Taxonomie](Documentation/taxonomie_normalisation.md)
- [Journal des changements](CHANGELOG.md)

## Statut des données

Le mémoire décrit un instantané de **1 153 documents**. Après retrait non destructif de 28 agrégats et rapports techniques vers `archive/`, la base principale contient **1 143 fiches JSON** au 31 août 2026. Cette différence doit être considérée comme une information de version : toute analyse future doit préciser sa date, son décompte et les sources incluses.

## Principes de continuité

- Ne pas écraser la base principale sans copie datée ou commit identifiable.
- Conserver données brutes, réponses LLM et sauvegardes : elles assurent l'audit et la provenance.
- Versionner ensemble prompt, modèle, paramètres d'inférence et taxonomie.
- Vérifier les données dans leur source avant publication ou analyse décisionnelle.
