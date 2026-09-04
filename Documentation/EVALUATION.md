# Évaluation

## Objectif

L'évaluation mesure l'accord entre des métadonnées automatiques et une référence humaine. Elle ne mesure pas la fréquence réelle des initiatives sur le territoire français.

## Référence existante

L'évaluation initiale repose sur 60 documents, avec dix documents par source. Les fichiers concernés sont dans `Evaluation/` :

- `llm_annotation_template.xlsx` : modèle d'annotation ;
- `annotation_guide.md` : consignes ;
- `llm_evaluation_results.csv` : résultats globaux ;
- `llm_evaluation_by_source.csv` : résultats par source ;
- `rule_based_vs_llm_comparison.csv` : comparaison baseline / LLM.

## Jugements

- `correct` : valeur prédite correcte ;
- `absence_correcte` : aucune valeur produite car le document ne permettait pas de la renseigner ;
- `incorrect` : valeur erronée ;
- `non_evaluable` : document ou réponse insuffisamment clair pour permettre un jugement fiable.

## Mesures

Pour les champs catégoriels, le score calcule précision, rappel et F1. La précision est la part de valeurs extraites correctes ; le rappel est la part des valeurs attendues retrouvées ; le F1 combine les deux sur une échelle de 0 à 1.

Un F1 proche de 1 indique un fort accord sur l'échantillon évalué, non une garantie universelle sur de nouvelles sources.

## Relancer l'évaluation

Copier le modèle, le remplir et l'enregistrer sous `Evaluation/llm_annotations_reviewer1.xlsx`, puis lancer :

```powershell
py .\Scripts\score_llm_annotations.py
py .\Scripts\score_rule_based_baseline.py
```

La priorité méthodologique est d'obtenir une seconde annotation indépendante, puis de mesurer l'accord inter-annotateur avant d'élargir les conclusions.
