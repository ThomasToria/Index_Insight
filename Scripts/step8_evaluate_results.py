from pathlib import Path
import json
import csv

PROJECT_ROOT = Path(r"C:\Users\PC\Desktop\Project_Internship\Index_Insight")

INPUT_FILE = PROJECT_ROOT / "Final_Tagged_Database" / "all_final_tagged_data.json"
OUTPUT_DIR = PROJECT_ROOT / "Evaluation"
OUTPUT_FILE = OUTPUT_DIR / "final_tagged_review.csv"

print("Projet :", PROJECT_ROOT)
print("Fichier attendu :", INPUT_FILE)
print("Existe :", INPUT_FILE.exists())

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FIELDS_TO_CHECK = [
    "titre",
    "territoire",
    "echelle",
    "public_vise",
    "porteur_initiative",
    "date",
    "thematique",
    "source_site"
]

DESCRIPTION_FIELDS = [
    "description_generale",
    "contexte",
    "problematique",
    "solution_envisagee",
    "objectifs"
]

def is_empty(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, list):
        return len(value) == 0
    if isinstance(value, dict):
        return len(value) == 0
    return False

def to_text(value):
    if isinstance(value, list):
        return " | ".join(str(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value) if value is not None else ""

def evaluate_record(record):
    confiance = record.get("confiance", {})
    description = record.get("description", {})

    empty_fields = []
    low_confidence_fields = []

    for field in FIELDS_TO_CHECK:
        value = record.get(field)
        conf = confiance.get(field, 0)

        if is_empty(value):
            empty_fields.append(field)

        if conf < 0.5:
            low_confidence_fields.append(field)

    for field in DESCRIPTION_FIELDS:
        value = description.get(field)
        conf = confiance.get(field, 0)

        if is_empty(value):
            empty_fields.append(field)

        if conf < 0.5:
            low_confidence_fields.append(field)

    total_fields = len(FIELDS_TO_CHECK) + len(DESCRIPTION_FIELDS)
    filled_fields = total_fields - len(empty_fields)
    completion_rate = round(filled_fields / total_fields, 2)

    average_confidence = round(
        sum(confiance.values()) / len(confiance),
        2
    ) if confiance else 0

    return {
        "empty_fields": empty_fields,
        "low_confidence_fields": low_confidence_fields,
        "completion_rate": completion_rate,
        "average_confidence": average_confidence
    }

def main():
    if not INPUT_FILE.exists():
        print(f"Fichier introuvable : {INPUT_FILE}")
        return

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        records = json.load(f)

    rows = []

    for record in records:
        evaluation = evaluate_record(record)
        description = record.get("description", {})

        row = {
            "fichier_source": record.get("fichier_source", ""),
            "source_site": record.get("source_site", ""),
            "titre": record.get("titre", ""),
            "territoire": record.get("territoire", ""),
            "echelle": to_text(record.get("echelle", [])),
            "public_vise": record.get("public_vise", ""),
            "porteur_initiative": record.get("porteur_initiative", ""),
            "date": to_text(record.get("date", [])),
            "thematique": to_text(record.get("thematique", [])),
            "description_generale": description.get("description_generale", ""),
            "contexte": description.get("contexte", ""),
            "problematique": description.get("problematique", ""),
            "solution_envisagee": description.get("solution_envisagee", ""),
            "objectifs": description.get("objectifs", ""),
            "completion_rate": evaluation["completion_rate"],
            "average_confidence": evaluation["average_confidence"],
            "empty_fields": " | ".join(evaluation["empty_fields"]),
            "low_confidence_fields": " | ".join(evaluation["low_confidence_fields"]),
            "validation_manuelle": "",
            "notes_correction": ""
        }

        rows.append(row)

    fieldnames = list(rows[0].keys()) if rows else []

    with OUTPUT_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    print("Évaluation terminée.")
    print(f"{len(rows)} ligne(s) écrite(s).")
    print(f"Fichier créé : {OUTPUT_FILE}")

if __name__ == "__main__":
    main()