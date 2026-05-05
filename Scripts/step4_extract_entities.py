from pathlib import Path
import json
import re

PROJECT_ROOT = Path(r"C:\Users\PC\Desktop\Project_Internship\Index_Insight")

INPUT_DIR = PROJECT_ROOT / "Sectioned_Database"
OUTPUT_DIR = PROJECT_ROOT / "Entities_Database"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MONTHS = (
    "janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|"
    "septembre|octobre|novembre|décembre|decembre"
)

DATE_PATTERNS = [
    rf"\b\d{{1,2}}\s+(?:{MONTHS})\s+\d{{4}}\b",
    rf"\b(?:{MONTHS})\s+\d{{4}}\b",
    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    r"\b\d{4}\b",
    r"\bdepuis\s+\d{4}\b",
    r"\ben\s+\d{4}\b",
    r"\bentre\s+\d{4}\s+et\s+\d{4}\b"
]

TERRITORY_PATTERNS = [
    r"\bà\s+([A-ZÉÈÀÂÊÎÔÛÇ][A-Za-zÀ-ÿ'’\- ]{2,80})",
    r"\bsur le territoire de\s+([A-ZÉÈÀÂÊÎÔÛÇ][A-Za-zÀ-ÿ'’\- ]{2,80})",
    r"\bdans la commune de\s+([A-ZÉÈÀÂÊÎÔÛÇ][A-Za-zÀ-ÿ'’\- ]{2,80})",
    r"\bdans le département de\s+([A-ZÉÈÀÂÊÎÔÛÇ][A-Za-zÀ-ÿ'’\- ]{2,80})",
    r"\bdans le département\s+([A-ZÉÈÀÂÊÎÔÛÇ][A-Za-zÀ-ÿ'’\- ]{2,80})",
    r"\ben région\s+([A-ZÉÈÀÂÊÎÔÛÇ][A-Za-zÀ-ÿ'’\- ]{2,80})",
    r"\bsitué(?:e)? à\s+([A-ZÉÈÀÂÊÎÔÛÇ][A-Za-zÀ-ÿ'’\- ]{2,80})"
]

ORG_KEYWORDS = [
    "association",
    "ccas",
    "cias",
    "mairie",
    "commune",
    "département",
    "région",
    "métropole",
    "fondation",
    "agence",
    "collectivité",
    "centre communal",
    "centre intercommunal",
    "ehpad",
    "résidence",
    "université",
    "hôpital",
    "chu"
]

ORG_PATTERNS = [
    r"\b(?:association|fondation|agence|mairie|commune|département|région|métropole|collectivité|ehpad|résidence|université|hôpital|chu|ccas|cias)\s+(?:de|du|des|d['’])?\s*([A-ZÉÈÀÂÊÎÔÛÇ][A-Za-zÀ-ÿ'’\- ]{2,80})",
    r"\b([A-ZÉÈÀÂÊÎÔÛÇ][A-Za-zÀ-ÿ'’\- ]{2,80})\s+(?:porte|pilote|organise|coordonne|anime|met en place)"
]

def unique_clean(items: list[str]) -> list[str]:
    cleaned = []

    for item in items:
        item = item.strip()
        item = re.split(r"[.;,\n]", item)[0].strip()
        item = re.sub(r"\s+", " ", item)

        if len(item) < 2:
            continue

        if item.lower() not in [x.lower() for x in cleaned]:
            cleaned.append(item)

    return cleaned

def extract_dates(text: str) -> list[str]:
    results = []

    for pattern in DATE_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        results.extend(matches)

    return unique_clean(results)

def extract_territories(text: str) -> list[str]:
    results = []

    for pattern in TERRITORY_PATTERNS:
        matches = re.findall(pattern, text)
        results.extend(matches)

    return unique_clean(results)

def extract_organizations(text: str) -> list[str]:
    results = []

    for pattern in ORG_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        for match in matches:
            if isinstance(match, tuple):
                results.extend([m for m in match if m])
            else:
                results.append(match)

    lines = text.splitlines()

    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ORG_KEYWORDS):
            if 5 <= len(line.strip()) <= 180:
                results.append(line.strip())

    return unique_clean(results)

def process_file(json_path: Path) -> dict:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    text_parts = []

    text_parts.extend(data.get("lignes", []))
    text_parts.extend(data.get("paragraphes", []))
    text_parts.extend(data.get("phrases", []))

    sections = data.get("sections_detectees", {})
    text_parts.extend(sections.values())

    full_text = "\n".join(text_parts)

    entities = {
        "dates_candidates": extract_dates(full_text),
        "territoires_candidates": extract_territories(full_text),
        "organisations_candidates": extract_organizations(full_text)
    }

    data["entites_candidates"] = entities

    if "stats" not in data:
        data["stats"] = {}

    data["stats"]["nombre_dates_candidates"] = len(entities["dates_candidates"])
    data["stats"]["nombre_territoires_candidates"] = len(entities["territoires_candidates"])
    data["stats"]["nombre_organisations_candidates"] = len(entities["organisations_candidates"])

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

            print(f"Entités extraites : {relative_path}")

        except Exception as e:
            print(f"Erreur avec {json_file} : {e}")

    print("\nExtraction des entités terminée.")
    print(f"Dossier de sortie : {OUTPUT_DIR}")

if __name__ == "__main__":
    main()