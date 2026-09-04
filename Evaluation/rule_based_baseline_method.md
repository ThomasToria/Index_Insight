# Rule-based baseline comparison

This evaluation compares the existing deterministic extraction workflow with
the local LLM on the same 60 documents already used for human evaluation.

## Inputs

- `Evaluation/llm_annotation_template.xlsx`: completed `Documents` and
  `Annotations` sheets. The `gold_value` cells are the human reference labels.
- `Final_Tagged_Database/`: historical rule-based JSON records.
- `Cleaned_Database/`: cleaned document text.
- `Evaluation/llm_evaluation_results.csv`: previously calculated LLM metrics.

## Fields and baseline definition

| Field | Rule-based prediction |
| --- | --- |
| `public_vise` | Historical free-text candidate from `Final_Tagged_Database`, deterministically mapped to the annotation vocabulary. |
| `echelle` | Historical scale labels from `Final_Tagged_Database`. |
| `nature_initiative` | Keyword-only extension applied to the first 2,500 characters of the cleaned document. The first matching category in the documented fixed order is returned. No LLM is called. |

The historical rule-based schema has no `nature_initiative` field. The third
row is therefore a transparent extension used solely for the comparison; it is
not represented as a historical database output.

## Run

From the project root:

```powershell
py .\Scripts\score_rule_based_baseline.py
```

To use a differently named completed annotation workbook:

```powershell
py .\Scripts\score_rule_based_baseline.py .\Evaluation\llm_annotations_reviewer1.xlsx
```

## Outputs

- `Evaluation/rule_based_baseline_results.csv`: rule-based precision, recall,
  micro/macro F1, and exact-match rate.
- `Evaluation/rule_based_vs_llm_comparison.csv`: paired table with both
  methods and the F1 difference.
- `Evaluation/rule_based_baseline_diagnostics.csv`: one row per document and
  field, including gold value, prediction, and raw rule output for inspection.

The results are a diagnostic comparison on a 60-document source-stratified
sample. They should not be interpreted as a population-level estimate or as an
independent blinded benchmark.
