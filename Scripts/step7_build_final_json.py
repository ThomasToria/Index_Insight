from pathlib import Path
import json

PROJECT_ROOT = Path(r"C:\Users\PC\Desktop\Project_Internship\Index_Insight")

INPUT_DIR = PROJECT_ROOT / "Scored_Database"
OUTPUT_DIR = PROJECT_ROOT / "Final_Tagged_Database"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_value(champs_scores: dict, field: str, default=""):
    return champs_scores.get(field, {}).get("valeur", default)

def get_confidence(champs_scores: dict, field: str) -> float:
    return champs_scores.get(field, {}).get("confiance", 0.0)

def build_final_record(data: dict, json_path: Path) -> dict:
    champs_scores = data.get("champs_scores", {})

    return {
        "titre": get_value(champs_scores, "titre"),
        "territoire": get_value(champs_scores, "territoire"),
        "echelle": get_value(champs_scores, "echelle", []),
        "public_vise": get_value(champs_scores, "public_vise"),
        "description": {
            "description_generale": get_value(champs_scores, "description"),
            "contexte": get_value(champs_scores, "contexte"),
            "problematique": get_value(champs_scores, "problematique"),
            "solution_envisagee": get_value(champs_scores, "solution_envisagee"),
            "objectifs": get_value(champs_scores, "objectifs")
        },
        "porteur_initiative": get_value(champs_scores, "porteur_initiative"),
        "date": get_value(champs_scores, "date", []),
        "thematique": get_value(champs_scores, "thematique", []),
        "source_site": get_value(champs_scores, "source_site"),
        "fichier_source": data.get("fichier_source", ""),
        "fichier_json_intermediaire": str(json_path),
        "confiance": {
            "titre": get_confidence(champs_scores, "titre"),
            "territoire": get_confidence(champs_scores, "territoire"),
            "echelle": get_confidence(champs_scores, "echelle"),
            "public_vise": get_confidence(champs_scores, "public_vise"),
            "description_generale": get_confidence(champs_scores, "description"),
            "contexte": get_confidence(champs_scores, "contexte"),
            "problematique": get_confidence(champs_scores, "problematique"),
            "solution_envisagee": get_confidence(champs_scores, "solution_envisagee"),
            "objectifs": get_confidence(champs_scores, "objectifs"),
            "porteur_initiative": get_confidence(champs_scores, "porteur_initiative"),
            "date": get_confidence(champs_scores, "date"),
            "thematique": get_confidence(champs_scores, "thematique"),
            "source_site": get_confidence(champs_scores, "source_site")
        }
    }

def process_file(json_path: Path) -> dict:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return build_final_record(data, json_path)

def main():
    json_files = list(INPUT_DIR.rglob("*.json"))

    if not json_files:
        print(f"Aucun fichier .json trouvé dans : {INPUT_DIR}")
        return

    print(f"{len(json_files)} fichier(s) trouvé(s).")

    all_records = []

    for json_file in json_files:
        try:
            final_record = process_file(json_file)
            all_records.append(final_record)

            relative_path = json_file.relative_to(INPUT_DIR)
            output_file = OUTPUT_DIR / relative_path
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with output_file.open("w", encoding="utf-8") as f:
                json.dump(final_record, f, ensure_ascii=False, indent=4)

            print(f"Finalisé : {relative_path}")

        except Exception as e:
            print(f"Erreur avec {json_file} : {e}")

    global_output = OUTPUT_DIR / "all_final_tagged_data.json"

    with global_output.open("w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=4)

    print("\nGénération finale terminée.")
    print(f"Dossier de sortie : {OUTPUT_DIR}")
    print(f"Fichier global : {global_output}")

if __name__ == "__main__":
    main()