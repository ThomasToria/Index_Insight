from pathlib import Path
import json
import re
import shutil
from datetime import datetime


print("SCRIPT LANCÉ")

BASE_DIR = Path(__file__).resolve().parents[1]
LLM_DIR = BASE_DIR / "LLM_Tagged_Database"
BACKUP_DIR = BASE_DIR / "LLM_Tagged_Database_backup_avant_harmonisation"

print(f"BASE_DIR : {BASE_DIR}")
print(f"LLM_DIR  : {LLM_DIR}")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def normalize_spaces(text):
    text = str(text).strip()
    return re.sub(r"\s+", " ", text)


def harmonize_territoire(value):
    territoires = []

    def clean_one(v):
        if v is None:
            return ""

        text = normalize_spaces(v).lower()

        text = text.replace("’", "'")
        text = text.replace("–", "-")
        text = text.replace("—", "-")

        text = re.sub(
            r"^(commune|communal|ville|territoire|département|departement|région|region|quartier|métropole|metropole|intercommunalité|intercommunalite|pays)\s*[:\-]\s*",
            "",
            text
        )

        text = re.sub(r"^commune de\s+", "", text)
        text = re.sub(r"^ville de\s+", "", text)
        text = re.sub(r"^territoire de\s+", "", text)
        text = re.sub(r"^département de\s+", "", text)
        text = re.sub(r"^departement de\s+", "", text)
        text = re.sub(r"^région de\s+", "", text)
        text = re.sub(r"^region de\s+", "", text)
        text = re.sub(r"^métropole de\s+", "", text)
        text = re.sub(r"^metropole de\s+", "", text)
        text = re.sub(r"^quartier de\s+", "", text)
        text = re.sub(r"^à\s+", "", text)
        text = re.sub(r"^a\s+", "", text)

        text = text.strip(" .,:;-")
        text = normalize_spaces(text)

        if text in {
            "communal", "communale", "departemental", "départemental",
            "regional", "régional", "national", "locale", "local",
            "non précisé", "non precise", "non renseigné", "non renseigne",
            "inconnu", "n/a"
        }:
            return ""

        return text

    if value is None:
        return []

    if isinstance(value, list):
        for item in value:
            territoires.extend(harmonize_territoire(item))

    elif isinstance(value, dict):
        for item in value.values():
            territoires.extend(harmonize_territoire(item))

    else:
        cleaned = clean_one(value)
        if cleaned:
            territoires.append(cleaned)

    return sorted(set(territoires))


MOIS_FR = {
    "janvier": "01", "février": "02", "fevrier": "02",
    "mars": "03", "avril": "04", "mai": "05",
    "juin": "06", "juillet": "07",
    "août": "08", "aout": "08",
    "septembre": "09", "octobre": "10",
    "novembre": "11", "décembre": "12", "decembre": "12"
}


def harmonize_date(value):
    if value is None:
        return []

    if isinstance(value, list):
        dates = []
        for item in value:
            dates.extend(harmonize_date(item))
        return sorted(set(dates))

    if isinstance(value, dict):
        dates = []
        for item in value.values():
            dates.extend(harmonize_date(item))
        return sorted(set(dates))

    text = normalize_spaces(value).lower()

    if not text:
        return []

    formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d"]

    for fmt in formats:
        try:
            date_obj = datetime.strptime(text, fmt)
            return [date_obj.strftime("%Y-%m-%d")]
        except ValueError:
            pass

    match = re.search(
        r"(\d{1,2})\s+(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(\d{4})",
        text
    )

    if match:
        day = match.group(1).zfill(2)
        month = MOIS_FR[match.group(2)]
        year = match.group(3)
        return [f"{year}-{month}-{day}"]

    years = re.findall(r"\b(19\d{2}|20\d{2})\b", text)

    return sorted(set(years))


def make_backup():
    if BACKUP_DIR.exists():
        print(f"Backup déjà existant : {BACKUP_DIR}")
        return

    print("Création d'une sauvegarde...")
    shutil.copytree(LLM_DIR, BACKUP_DIR)
    print(f"Sauvegarde créée : {BACKUP_DIR}")


def main():
    print("Début du traitement...")

    if not LLM_DIR.exists():
        print(f"ERREUR : dossier introuvable : {LLM_DIR}")
        return

    make_backup()

    json_files = list(LLM_DIR.rglob("*.json"))
    print(f"{len(json_files)} fichiers JSON trouvés.")

    modified_count = 0
    error_count = 0

    for json_path in json_files:
        try:
            data = load_json(json_path)

            if not isinstance(data, dict):
                continue

            old_territoire = data.get("territoire")
            old_date = data.get("date")

            new_territoire = harmonize_territoire(old_territoire)
            new_date = harmonize_date(old_date)

            changed = False

            if old_territoire != new_territoire:
                data["territoire"] = new_territoire
                changed = True

            if old_date != new_date:
                data["date"] = new_date
                changed = True

            if changed:
                save_json(json_path, data)
                modified_count += 1
                print(f"Modifié : {json_path.name}")

        except Exception as e:
            error_count += 1
            print(f"Erreur avec {json_path.name} : {e}")

    print("\nTerminé.")
    print(f"Fichiers modifiés : {modified_count}")
    print(f"Erreurs : {error_count}")
    print(f"Sauvegarde : {BACKUP_DIR}")


if __name__ == "__main__":
    main()