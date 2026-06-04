from pathlib import Path
import json

PROJECT_ROOT = Path(r"C:\Users\PC\Desktop\Project_Internship\Index_Insight")

JSON_ROOT = PROJECT_ROOT / "LLM_Tagged_Database"

CATEGORY_NAME = "statut_action"

REALISE = "projet réalisé"
PROPOSITION = "proposition de projet"

def get_statut_action(json_path: Path) -> str:
    if "Fiches_actions_database" in json_path.parts:
        return PROPOSITION
    return REALISE

def update_json_file(json_path: Path) -> bool:
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        statut = get_statut_action(json_path)

        if isinstance(data, dict):
            if data.get(CATEGORY_NAME) == statut:
                return False

            data[CATEGORY_NAME] = statut

            with json_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            return True

        return False

    except Exception as e:
        print(f"ERREUR avec {json_path}: {e}")
        return False

def main():
    json_files = [
        p for p in JSON_ROOT.rglob("*.json")
        if not p.name.startswith("all_")
        and not p.name.startswith("errors_")
        and not p.name.startswith("new_or_updated_")
    ]

    updated = 0
    skipped = 0

    print(f"{len(json_files)} fichier(s) JSON trouvé(s)")
    print(f"Dossier analysé : {JSON_ROOT}")

    for json_file in json_files:
        changed = update_json_file(json_file)

        if changed:
            updated += 1
            print(f"Mis à jour : {json_file}")
        else:
            skipped += 1

    print("\nTerminé")
    print(f"Fichiers mis à jour : {updated}")
    print(f"Fichiers ignorés : {skipped}")

if __name__ == "__main__":
    main()