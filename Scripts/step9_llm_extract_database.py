from pathlib import Path
import json
import re
import requests # type: ignore
from tqdm import tqdm # type: ignore

PROJECT_ROOT = Path(r"C:\Users\PC\Desktop\Project_Internship\Index_Insight")

INPUT_DIR = PROJECT_ROOT / "Cleaned_Database" / "Vada_database"
OUTPUT_DIR = PROJECT_ROOT / "LLM_Tagged_Database" / "Vada_database"

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:1.5b"

MAX_CHARS = 2500

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_KEYS = [
    "titre",
    "territoire",
    "echelle",
    "public_vise",
    "nature_initiative",
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

def get_source_site(txt_path: Path) -> str:
    return "VADA"

def has_nature_initiative(obj):
    if isinstance(obj, dict):
        if "nature_initiative" in obj:
            return True
        return any(has_nature_initiative(value) for value in obj.values())

    if isinstance(obj, list):
        return any(has_nature_initiative(item) for item in obj)

    return False

def should_skip_file(output_file: Path) -> bool:
    if not output_file.exists():
        return False

    try:
        with output_file.open("r", encoding="utf-8") as f:
            existing_json = json.load(f)

        return has_nature_initiative(existing_json)

    except Exception:
        return False

def empty_record(source_site: str) -> dict:
    return {
        "titre": "",
        "territoire": "",
        "echelle": [],
        "public_vise": "public non connu",
        "nature_initiative": "",
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
  "nature_initiative": "",
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

Règles générales :
- N'invente rien.
- Tu peux déduire une information seulement si elle est fortement implicite dans le texte.
- Si une information est absente ou impossible à déduire clairement, mets "" ou [].
- source_site doit être exactement "{source_site}".

Règles pour "public_vise" :
- public_vise doit contenir une seule valeur parmi :
  "ainés",
  "ainés et autres",
  "professionnels",
  "autre",
  "public non connu".
- Utilise "ainés" si le texte vise principalement des personnes âgées, seniors, retraités, résidents d’EHPAD ou aînés.
- Utilise "ainés et autres" si les personnes âgées sont concernées avec d’autres publics : familles, aidants, grand public, professionnels, voisins, scolaires, etc.
- Utilise "professionnels" si le texte vise principalement des agents, services techniques, établissements, responsables, soignants ou autres professionnels.
- Utilise "autre" si le public est identifiable mais ne correspond pas aux catégories précédentes.
- Utilise "public non connu" si le public n’est pas identifiable.

Règles pour "nature_initiative" :
- Indique la nature principale de l’initiative.
- Exemples possibles :
  "atelier",
  "formation",
  "sensibilisation",
  "enquête",
  "rapport",
  "plaidoyer",
  "outil numérique",
  "événement",
  "accompagnement",
  "dispositif",
  "publication",
  "offre de service",
  "groupe de parole",
  "lieu / espace dédié",
  "projet d'aménagement",
  "autre".
- Si plusieurs natures sont possibles, choisis la plus représentative.

Règles pour "echelle" :
- echelle doit être une liste.
- echelle doit contenir seulement :
  "quartier",
  "communale",
  "intercommunale",
  "départementale",
  "régionale",
  "nationale",
  "internationale".
- Si le texte mentionne une ville ou une commune, utilise "communale".
- Si le texte mentionne une métropole, une intercommunalité ou plusieurs communes, utilise "intercommunale".
- Si le texte mentionne un département, utilise "départementale".
- Si le texte mentionne une région, utilise "régionale".
- Si le texte mentionne une portée nationale ou un organisme national, utilise "nationale".

Règles pour "date" :
- date doit être une liste.
- Repère toutes les dates explicites, même approximatives.
- Conserve les formulations temporelles utiles telles qu’elles apparaissent dans le texte.
- Exemples acceptés :
  ["2019"],
  ["depuis 2019"],
  ["mars 2016"],
  ["fin janvier 2025"],
  ["25/01/2018"],
  ["19 mai 2017"].
- Ne transforme pas forcément les dates approximatives en format ISO.
- Si le texte dit "disponible depuis 2019", la date doit contenir "depuis 2019".
- Si le texte dit "enquête lancée fin janvier", la date doit contenir "fin janvier" ou "fin janvier 2025" si l’année est déductible.

Règles pour "porteur_initiative" :
- Identifie l’acteur qui porte, organise, lance, pilote ou met en œuvre l’initiative.
- Si le texte indique qu’un EHPAD, une résidence, une association, une ville, une métropole, une caisse ou une fondation organise l’action, utilise cet acteur.
- Exemple : si le texte indique que l’action concerne les 30 ans de l’EHPAD « La Résidence de l’Ille » et que la direction/personnel de l’établissement organise la journée, le porteur peut être "EHPAD La Résidence de l’Ille".
- Ne laisse vide que si aucun porteur n’est identifiable ou fortement déductible.

Règles pour "problematique" :
- La problématique doit exprimer le problème, besoin ou enjeu auquel répond l’initiative.
- Elle peut être déduite à partir des objectifs, du contexte ou des obstacles mentionnés.
- Ne recopie pas seulement l’objectif si une problématique peut être formulée.
- Exemple : pour une action autour des 30 ans d’un EHPAD visant les échanges intergénérationnels et la valorisation des résidents, une problématique possible est :
  "Le besoin de renforcer les liens entre les résidents de l’EHPAD, leurs proches et la société civile, tout en valorisant leur mémoire et leur place dans la vie locale."

Règles pour "thematique" :
- thematique doit être une liste.
- Utilise des intitulés courts et homogènes.
- Évite les doublons dus aux majuscules/minuscules.
- Préfère par exemple :
  "santé",
  "mobilité",
  "lien social",
  "numérique",
  "habitat",
  "prévention",
  "intergénérationnel",
  "isolement",
  "participation citoyenne".

Texte :
{text}
""".strip()

def call_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Tu réponds uniquement avec un JSON strictement valide. Aucun texte hors JSON."
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
            "num_predict": 700,
            "num_ctx": 8192
        }
    }

    response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=900)
    response.raise_for_status()
    return response.json()["message"]["content"]

def save_raw_response(txt_path: Path, response_text: str):
    relative_path = txt_path.relative_to(INPUT_DIR)
    raw_file = OUTPUT_DIR / "_raw_responses" / relative_path.with_suffix(".txt")
    raw_file.parent.mkdir(parents=True, exist_ok=True)
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

def clean_list(values):
    if values is None:
        return []

    if not isinstance(values, list):
        values = [values]

    cleaned = []
    seen = set()

    for value in values:
        value = str(value).strip()
        if not value:
            continue

        key = value.lower()
        if key not in seen:
            cleaned.append(value)
            seen.add(key)

    return cleaned

def normalize_public_vise(value: str) -> str:
    allowed = {
        "ainés",
        "ainés et autres",
        "professionnels",
        "autre",
        "public non connu"
    }

    value = str(value).strip().lower()

    replacements = {
        "aînés": "ainés",
        "aines": "ainés",
        "seniors": "ainés",
        "personnes âgées": "ainés",
        "personnes agees": "ainés",
        "retraités": "ainés",
        "retraites": "ainés",
        "professionnel": "professionnels",
        "professionnels": "professionnels",
        "inconnu": "public non connu",
        "non connu": "public non connu",
        "public inconnu": "public non connu"
    }

    value = replacements.get(value, value)

    if value in allowed:
        return value

    return "public non connu"

def normalize_echelle(values):
    allowed = {
        "quartier",
        "communale",
        "intercommunale",
        "départementale",
        "régionale",
        "nationale",
        "internationale"
    }

    replacements = {
        "departementale": "départementale",
        "régional": "régionale",
        "regional": "régionale",
        "regionale": "régionale",
        "national": "nationale",
        "international": "internationale",
        "communal": "communale"
    }

    cleaned = []

    for value in clean_list(values):
        v = value.strip().lower()
        v = replacements.get(v, v)

        if v in allowed and v not in cleaned:
            cleaned.append(v)

    return cleaned

def normalize(record: dict, source_site: str) -> dict:
    if "problématique" in record and "problematique" not in record:
        record["problematique"] = record["problématique"]

    if "thématique" in record and "thematique" not in record:
        record["thematique"] = record["thématique"]

    if "nature de l'initiative" in record and "nature_initiative" not in record:
        record["nature_initiative"] = record["nature de l'initiative"]

    if "nature_initiative" not in record and "nature" in record:
        record["nature_initiative"] = record["nature"]

    base = empty_record(source_site)

    for key in base:
        if key in record:
            base[key] = record[key]

    base["echelle"] = normalize_echelle(base["echelle"])
    base["date"] = clean_list(base["date"])
    base["thematique"] = clean_list(base["thematique"])
    base["public_vise"] = normalize_public_vise(base["public_vise"])
    base["source_site"] = source_site

    return base

def rebuild_nested_description(record: dict) -> dict:
    return {
        "titre": record["titre"],
        "territoire": record["territoire"],
        "echelle": record["echelle"],
        "public_vise": record["public_vise"],
        "nature_initiative": record["nature_initiative"],
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
    text = txt_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )[:MAX_CHARS]

    source_site = get_source_site(txt_path)

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
    txt_files = list(INPUT_DIR.rglob("*.txt"))

    if not txt_files:
        print(f"Aucun fichier .txt trouvé dans : {INPUT_DIR}")
        return

    print(f"{len(txt_files)} fichier(s) trouvé(s)")
    print(f"Modèle : {MODEL}")
    print("Mode : ignore les JSON qui contiennent déjà nature_initiative")

    results = []
    errors = []
    skipped = 0

    for txt_file in tqdm(
        txt_files,
        desc="LLM extraction VADA",
        unit="fichier"
    ):
        try:
            relative_path = txt_file.relative_to(INPUT_DIR)
            output_file = OUTPUT_DIR / relative_path.with_suffix(".json")

            if should_skip_file(output_file):
                skipped += 1
                tqdm.write(f"Déjà au nouveau format, ignoré : {txt_file.name}")
                continue

            tqdm.write(f"→ {relative_path}")

            data = process_file(txt_file)
            results.append(data)

            output_file.parent.mkdir(parents=True, exist_ok=True)

            with output_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            tqdm.write(f"OK : {output_file}")

        except Exception as e:
            error = {
                "fichier": str(txt_file),
                "erreur": str(e)
            }
            errors.append(error)
            tqdm.write(f"ERREUR avec {txt_file.name}: {e}")

    global_output = OUTPUT_DIR / "new_or_updated_vada_llm.json"

    with global_output.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    error_output = OUTPUT_DIR / "errors_llm.json"

    with error_output.open("w", encoding="utf-8") as f:
        json.dump(errors, f, indent=4, ensure_ascii=False)

    print("\nTerminé")
    print(f"Fichiers ignorés déjà au nouveau format : {skipped}")
    print(f"Fichiers traités ou retraités : {len(results)}")
    print(f"Erreurs : {len(errors)}")
    print(f"Fichier global des nouveaux/retraités : {global_output}")
    print(f"Rapport erreurs : {error_output}")
    print(f"Réponses brutes : {OUTPUT_DIR / '_raw_responses'}")

if __name__ == "__main__":
    main()