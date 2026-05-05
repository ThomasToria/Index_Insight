from pathlib import Path
import json
import re

PROJECT_ROOT = Path(r"C:\Users\PC\Desktop\Project_Internship\Index_Insight")

INPUT_DIR = PROJECT_ROOT / "Segmented_Database"
OUTPUT_DIR = PROJECT_ROOT / "Sectioned_Database"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SECTION_PATTERNS = {
    "titre": [
        r"^titre$",
        r"^nom de l['’]action$",
        r"^intitulé$",
        r"^intitulé de l['’]action$"
    ],
    "territoire": [
        r"^territoire$",
        r"^lieu$",
        r"^localisation$",
        r"^zone géographique$",
        r"^périmètre$"
    ],
    "public_vise": [
        r"^public$",
        r"^public visé$",
        r"^bénéficiaires$",
        r"^participants$",
        r"^personnes concernées$"
    ],
    "description": [
        r"^description$",
        r"^présentation$",
        r"^résumé$",
        r"^descriptif$"
    ],
    "contexte": [
        r"^contexte$",
        r"^diagnostic$",
        r"^constat$"
    ],
    "problematique": [
        r"^problématique$",
        r"^problematique$",
        r"^enjeux$",
        r"^enjeu$",
        r"^besoin identifié$"
    ],
    "solution_envisagee": [
        r"^solution$",
        r"^solution envisagée$",
        r"^actions mises en place$",
        r"^modalités de mise en œuvre$",
        r"^mise en œuvre$",
        r"^déroulement$"
    ],
    "objectifs": [
        r"^objectif$",
        r"^objectifs$",
        r"^finalité$",
        r"^finalités$",
        r"^ambition$"
    ],
    "porteur_initiative": [
        r"^porteur$",
        r"^porteur de l['’]initiative$",
        r"^structure porteuse$",
        r"^organisme porteur$",
        r"^acteur porteur$"
    ],
    "date": [
        r"^date$",
        r"^année$",
        r"^calendrier$",
        r"^période$"
    ],
    "thematique": [
        r"^thématique$",
        r"^theme$",
        r"^thème$",
        r"^catégorie$",
        r"^axe$"
    ]
}

def normalize_heading(line: str) -> str:
    line = line.strip().lower()
    line = re.sub(r"[:\-–—]+$", "", line)
    line = re.sub(r"\s+", " ", line)
    return line

def detect_section_name(line: str) -> str | None:
    normalized = normalize_heading(line)

    for section_name, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, normalized):
                return section_name

    return None

def extract_sections(lines: list[str]) -> dict:
    sections = {}
    current_section = None

    for line in lines:
        detected = detect_section_name(line)

        if detected:
            current_section = detected
            if current_section not in sections:
                sections[current_section] = []
            continue

        if current_section:
            sections[current_section].append(line)

    return {key: "\n".join(value).strip() for key, value in sections.items() if value}

def process_file(json_path: Path) -> dict:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    lines = data.get("lignes", [])
    sections = extract_sections(lines)

    data["sections_detectees"] = sections
    data["stats"]["nombre_sections_detectees"] = len(sections)

    return data

def main():
    json_files = list(INPUT_DIR.rglob("*.json"))

    if not json_files:
        print(f"Aucun fichier .json trouvé dans : {INPUT_DIR}")
        return

    print(f"{len(json_files)} fichier(s) trouvé(s).")

    for json_file in json_files:
        try:
            enriched_data = process_file(json_file)

            relative_path = json_file.relative_to(INPUT_DIR)
            output_file = OUTPUT_DIR / relative_path
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with output_file.open("w", encoding="utf-8") as f:
                json.dump(enriched_data, f, ensure_ascii=False, indent=4)

            print(f"Sections détectées : {relative_path}")

        except Exception as e:
            print(f"Erreur avec {json_file} : {e}")

    print("\nDétection des sections terminée.")
    print(f"Dossier de sortie : {OUTPUT_DIR}")

if __name__ == "__main__":
    main()