from pathlib import Path
import json
import re
import time
import requests
from tqdm import tqdm

PROJECT_ROOT = Path(r"C:\Users\PC\Desktop\Project_Internship\Index_Insight")

INPUT_DIR = PROJECT_ROOT / "Cleaned_Database"
OUTPUT_DIR = PROJECT_ROOT / "LLM_Tagged_Database"

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:3b"

MAX_FILES = 5
MAX_CHARS = 800

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_MAPPING = {
    "Cnav_database": "CNAV",
    "cnsa_database": "CNSA",
    "FdF_database": "Fondation de France",
    "Fiches_actions_database": "Fiches actions",
    "Hcfea_database": "HCFEA",
    "iresp_autonomie_database": "IRESP Autonomie",
    "Vada_database": "VADA"
}

EXPECTED_KEYS = [
    "titre",
    "territoire",
    "echelle",
    "public_vise",
    "description_generale",
    "contexte",
    "problematique",
    "solution_envisagee",
    "objectifs",
    "porteur_initiative",
    "date",
    "thematique",
    "source_site"
]

def detect_source_site(txt_path: Path) -> str:
    for part in txt_path.parts:
        if part in SOURCE_MAPPING:
            return SOURCE_MAPPING[part]
    return ""

def empty_record(source_site: str) -> dict:
    return {
        "titre": "",
        "territoire": "",
        "echelle": [],
        "public_vise": "",
        "description_generale": "",
        "contexte": "",
        "problematique": "",
        "solution_envisagee": "",
        "objectifs": "",
        "porteur_initiative": "",
        "date": [],
        "thematique": [],
        "source_site": source_site
    }

def build_prompt(text: str, source_site: str) -> str:
    return f"""
Retourne uniquement un JSON strictement valide.
Aucun markdown. Aucun commentaire. Aucun texte avant ou après.

Les clés JSON doivent être exactement celles-ci, sans accent :
{", ".join(EXPECTED_KEYS)}

Interdiction de renommer les clés.
Utilise "problematique" sans accent.
Utilise "thematique" sans accent.

Structure obligatoire :
{{
  "titre": "",
  "territoire": "",
  "echelle": [],
  "public_vise": "",
  "description_generale": "",
  "contexte": "",
  "problematique": "",
  "solution_envisagee": "",
  "objectifs": "",
  "porteur_initiative": "",
  "date": [],
  "thematique": [],
  "source_site": "{source_site}"
}}

Règles :
- N'invente rien.
- Si une information est absente, mets "" ou [].
- source_site doit être exactement "{source_site}".
- echelle doit contenir seulement : quartier, communale, intercommunale, départementale, régionale, nationale, internationale.
- date doit être une liste.
- thematique doit être une liste.
- echelle doit être une liste.

Texte :
{text}
""".strip()

def call_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Tu réponds uniquement avec un JSON valide. Aucun texte hors JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "num_predict": 500,
            "num_ctx": 2048
        }
    }

    response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=240)
    response.raise_for_status()
    return response.json()["message"]["content"]

def save_raw_response(txt_path: Path, response_text: str):
    raw_dir = OUTPUT_DIR / "_raw_responses"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / f"{txt_path.stem}_raw.txt"
    raw_file.write_text(response_text, encoding="utf-8")

def repair_json_text(text: str) -> str:
    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1:
        text = text[start:]

    if end != -1:
        text = text[:end + 1]

    text = text.replace("“", "\"").replace("”", "\"")
    text = text.replace("’", "'")
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)

    open_braces = text.count("{")
    close_braces = text.count("}")

    if open_braces > close_braces:
        text += "}" * (open_braces - close_braces)

    return text

def extract_json(response_text: str) -> dict:
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        repaired = repair_json_text(response_text)
        return json.loads(repaired)

def normalize(record: dict, source_site: str) -> dict:
    if "problématique" in record and "problematique" not in record:
        record["problematique"] = record["problématique"]

    if "thématique" in record and "thematique" not in record:
        record["thematique"] = record["thématique"]

    base = empty_record(source_site)

    for key in base:
        if key in record:
            base[key] = record[key]

    if not isinstance(base["echelle"], list):
        base["echelle"] = [str(base["echelle"])]

    if not isinstance(base["date"], list):
        base["date"] = [str(base["date"])]

    if not isinstance(base["thematique"], list):
        base["thematique"] = [str(base["thematique"])]

    base["source_site"] = source_site

    return base

def rebuild_nested_description(record: dict) -> dict:
    return {
        "titre": record["titre"],
        "territoire": record["territoire"],
        "echelle": record["echelle"],
        "public_vise": record["public_vise"],
        "description": {
            "description_generale": record["description_generale"],
            "contexte": record["contexte"],
            "problematique": record["problematique"],
            "solution_envisagee": record["solution_envisagee"],
            "objectifs": record["objectifs"]
        },
        "porteur_initiative": record["porteur_initiative"],
        "date": record["date"],
        "thematique": record["thematique"],
        "source_site": record["source_site"]
    }

def process_file(txt_path: Path) -> dict:
    text = txt_path.read_text(encoding="utf-8", errors="ignore")[:MAX_CHARS]
    source_site = detect_source_site(txt_path)

    prompt = build_prompt(text, source_site)
    response_text = call_ollama(prompt)

    save_raw_response(txt_path, response_text)

    parsed = extract_json(response_text)
    flat_record = normalize(parsed, source_site)
    final_record = rebuild_nested_description(flat_record)

    final_record["fichier_source"] = str(txt_path)
    final_record["nom_fichier"] = txt_path.name

    return final_record

def main():
    txt_files = list(INPUT_DIR.rglob("*.txt"))[:MAX_FILES]

    if not txt_files:
        print(f"Aucun fichier .txt trouvé dans : {INPUT_DIR}")
        return

    print(f"{len(txt_files)} fichiers test")
    print(f"Modèle : {MODEL}")

    results = []

    for txt_file in tqdm(txt_files, desc="LLM extraction", unit="fichier"):
        try:
            tqdm.write(f"→ {txt_file.name}")

            data = process_file(txt_file)
            results.append(data)

            relative_path = txt_file.relative_to(INPUT_DIR)
            output_file = OUTPUT_DIR / relative_path.with_suffix(".json")
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with output_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            tqdm.write(f"OK : {output_file}")

        except Exception as e:
            tqdm.write(f"ERREUR avec {txt_file.name}: {e}")

        time.sleep(0.3)

    global_output = OUTPUT_DIR / "all_llm_test.json"

    with global_output.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print("\nTerminé")
    print(f"Fichier global : {global_output}")
    print(f"Réponses brutes : {OUTPUT_DIR / '_raw_responses'}")

if __name__ == "__main__":
    main()