from pathlib import Path
import json
from collections import Counter

PROJECT_ROOT = Path(r"C:\Users\PC\Desktop\Project_Internship\Index_Insight")

JSON_DIR = PROJECT_ROOT / "LLM_Tagged_Database"
OUTPUT_FILE = PROJECT_ROOT / "stats_thematiques_natures.txt"


EXCLUDED_FILES = {
    "errors_llm.json",
    "errors_nature_initiative.json",
    "errors_nature_thematique.json",
    "errors_hybrid_nature_thematique.json",
    "updated_nature_initiative.json",
    "updated_nature_thematique.json",
    "updated_hybrid_nature_thematique.json",
    "new_or_updated_vada_llm.json"
}


def normalize_text(value):
    return str(value).strip().lower()


def load_json_file(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_thematiques(data):
    thematiques = data.get("thematique", [])

    if isinstance(thematiques, str):
        thematiques = [thematiques]

    if not isinstance(thematiques, list):
        return []

    return [
        normalize_text(t)
        for t in thematiques
        if str(t).strip()
    ]


def extract_nature(data):
    nature = data.get("nature_initiative", "")

    if not isinstance(nature, str):
        return ""

    return normalize_text(nature)


def main():
    json_files = [
        file for file in JSON_DIR.rglob("*.json")
        if file.name not in EXCLUDED_FILES
    ]

    thematique_counter = Counter()
    nature_counter = Counter()

    total_files = 0
    files_with_thematique = 0
    files_with_nature = 0
    errors = []

    for json_file in json_files:
        try:
            data = load_json_file(json_file)

            if not isinstance(data, dict):
                continue

            total_files += 1

            thematiques = extract_thematiques(data)
            nature = extract_nature(data)

            if thematiques:
                files_with_thematique += 1
                thematique_counter.update(thematiques)

            if nature:
                files_with_nature += 1
                nature_counter.update([nature])

        except Exception as e:
            errors.append({
                "fichier": str(json_file),
                "erreur": str(e)
            })

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        f.write("STATISTIQUES DES THÉMATIQUES ET NATURES D'INITIATIVES\n")
        f.write("=" * 60 + "\n\n")

        f.write("RÉSUMÉ GLOBAL\n")
        f.write("-" * 60 + "\n")
        f.write(f"Fichiers JSON analysés : {total_files}\n")
        f.write(f"Fichiers avec thématique : {files_with_thematique}\n")
        f.write(f"Nombre de thématiques différentes : {len(thematique_counter)}\n")
        f.write(f"Fichiers avec nature_initiative : {files_with_nature}\n")
        f.write(f"Nombre de natures différentes : {len(nature_counter)}\n")
        f.write(f"Erreurs : {len(errors)}\n\n")

        f.write("OCCURRENCES DES THÉMATIQUES\n")
        f.write("=" * 60 + "\n\n")

        for theme, count in thematique_counter.most_common():
            f.write(f"{theme} : {count}\n")

        f.write("\n\n")
        f.write("OCCURRENCES DES NATURES D'INITIATIVES\n")
        f.write("=" * 60 + "\n\n")

        for nature, count in nature_counter.most_common():
            f.write(f"{nature} : {count}\n")

        if errors:
            f.write("\n\n")
            f.write("ERREURS\n")
            f.write("=" * 60 + "\n\n")

            for error in errors:
                f.write(f"{error['fichier']} : {error['erreur']}\n")

    print("Terminé.")
    print(f"Fichiers JSON analysés : {total_files}")
    print(f"Fichiers avec thématique : {files_with_thematique}")
    print(f"Thématiques différentes : {len(thematique_counter)}")
    print(f"Fichiers avec nature_initiative : {files_with_nature}")
    print(f"Natures différentes : {len(nature_counter)}")
    print(f"Erreurs : {len(errors)}")
    print(f"Résultat écrit dans : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()