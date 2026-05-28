from pathlib import Path
import json
from collections import Counter

PROJECT_ROOT = Path(r"C:\Users\PC\Desktop\Project_Internship\Index_Insight")

INPUT_DIR = PROJECT_ROOT / "LLM_Tagged_Database"
OUTPUT_FILE = PROJECT_ROOT / "thematiques_occurrences.txt"

def extract_thematiques(data):
    thematiques = data.get("thematique", [])

    if isinstance(thematiques, str):
        thematiques = [thematiques]

    if not isinstance(thematiques, list):
        return []

    return [
    str(t).strip().lower()
    for t in thematiques
    if str(t).strip()
]

def main():
    counter = Counter()
    total_files = 0
    files_with_thematiques = 0

    json_files = [
        p for p in INPUT_DIR.rglob("*.json")
        if not p.name.startswith("all_")
        and "_raw_responses" not in p.parts
        and "_errors" not in p.parts
    ]

    for json_file in json_files:
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            total_files += 1
            thematiques = extract_thematiques(data)

            if thematiques:
                files_with_thematiques += 1
                counter.update(thematiques)

        except Exception as e:
            print(f"Erreur avec {json_file}: {e}")

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        f.write("Liste des thématiques avec occurrences\n")
        f.write("=" * 45 + "\n\n")
        f.write(f"Fichiers JSON analysés : {total_files}\n")
        f.write(f"Fichiers avec thématique : {files_with_thematiques}\n")
        f.write(f"Nombre de thématiques différentes : {len(counter)}\n\n")

        for thematique, count in counter.most_common():
            f.write(f"{thematique} : {count}\n")

    print("Terminé")
    print(f"Fichiers JSON analysés : {total_files}")
    print(f"Thématiques différentes : {len(counter)}")
    print(f"Fichier créé : {OUTPUT_FILE}")

if __name__ == "__main__":
    main()