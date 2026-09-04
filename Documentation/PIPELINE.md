# Pipeline Index_Insight

## Vue d'ensemble

```text
Sources web et PDF
        ↓
Collecte / conversion en texte
        ↓
Database/ → Cleaned_Database/
        ↓
Préparation et scoring historique
        ↓
Extraction LLM locale
        ↓
LLM_Tagged_Database/  ← base principale
        ↓
Normalisation, provenance, exports et évaluation humaine
```

## Étapes principales

### 1. Collecte et préparation

Les scripts `*_scrap.py`, `*_scraping.py`, `Docx_to_txt.py`, `step1_clean_fiches_actions.py` et `filename_cleaner.py` produisent ou préparent les textes de `Cleaned_Database/`. Pour toute nouvelle collecte, conserver l'URL, le titre original, la date de collecte et le nom de la source.

### 2. Baseline rule-based historique

Les scripts `step2_` à `step8_` alimentent les dossiers intermédiaires et `Final_Tagged_Database/`. Ils sont conservés pour la reproductibilité et la comparaison, mais ne constituent pas la base de production.

### 3. Extraction LLM

`Scripts/step9_llm_extract_database.py` interroge Ollama et écrit les JSON dans `LLM_Tagged_Database/`. Avant une exécution complète, noter le modèle, la version du prompt, la taille maximale de texte, les sources traitées et la date d'exécution. Créer une copie datée ou un commit avant d'écraser des données existantes.

### 4. Normalisation

Toujours commencer par :

```powershell
py .\Scripts\normaliser_taxonomie.py --dry-run
```

Lire le rapport de valeurs à revoir puis appliquer après validation :

```powershell
py .\Scripts\normaliser_taxonomie.py --apply
```

Les champs bruts sont conservés ; le script ajoute `thematique_normalisee`, `nature_initiative_normalisee` et `version_taxonomie`.

### 5. Contrôle et évaluation

```powershell
py .\Scripts\validate_llm_database.py
py .\Scripts\score_llm_annotations.py
py .\Scripts\score_rule_based_baseline.py
```

Le validateur ne modifie pas les JSON. Les scripts d'évaluation requièrent le classeur d'annotation complété décrit dans [EVALUATION.md](EVALUATION.md).

Pour les corrections déterministes fondées sur la provenance, exécuter d'abord `py .\Scripts\repair_metadata_from_provenance.py`, relire le rapport, puis ajouter `--apply` seulement si les changements conviennent.
