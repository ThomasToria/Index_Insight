from pathlib import Path
import json
import re
import requests # type: ignore
from tqdm import tqdm # type: ignore
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(r"C:\Users\PC\Desktop\Project_Internship\Index_Insight")

JSON_DIR = PROJECT_ROOT / "LLM_Tagged_Database" / "iresp_autonomie_database"
TEXT_DIR = PROJECT_ROOT / "Cleaned_Database" / "iresp_autonomie_database"

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:1.5b"

MAX_CHARS = 1200
MAX_WORKERS = 4

ALLOWED_NATURES = [
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
    "consultation citoyenne",
    "lieu / espace dédié",
    "projet d'aménagement",
    "autre"
]

THEMATIQUE_KEYWORDS = {
    "santé et prévention": [
        "santé", "prévention", "soin", "médical", "médecin", "maladie",
        "alzheimer", "dépression", "chute", "santé mentale", "bien-être"
    ],
    "autonomie et grand âge": [
        "autonomie", "grand âge", "vieillissement", "personnes âgées",
        "seniors", "aînés", "retraités", "ehpad", "résidence autonomie"
    ],
    "handicap et aidants": [
        "handicap", "aidant", "aidants", "aidants familiaux", "autisme",
        "aphasie", "paralysie", "traumatisme crânien"
    ],
    "lien social et isolement": [
        "lien social", "isolement", "solidarité", "cohésion sociale",
        "inclusion sociale", "vie sociale", "rencontre", "convivialité"
    ],
    "intergénérationnel": [
        "intergénérationnel", "intergénérationnelle", "jeunes et seniors",
        "enfants", "scolaires", "élèves"
    ],
    "mobilité et transport": [
        "mobilité", "transport", "transports", "déplacement", "déplacements",
        "sécurité routière", "marche urbaine"
    ],
    "habitat et logement": [
        "habitat", "logement", "habitat social", "domicile", "résidence",
        "adaptation du logement"
    ],
    "numérique": [
        "numérique", "digital", "application", "plateforme", "site internet",
        "outil numérique", "technologie", "informatique"
    ],
    "participation citoyenne": [
        "participation citoyenne", "consultation", "concertation",
        "décisions participatives", "engagement des habitants",
        "citoyen", "citoyenne"
    ],
    "culture et loisirs": [
        "culture", "loisirs", "art", "créativité", "patrimoine",
        "histoire locale", "mémoire", "sortie"
    ],
    "activité physique et sport": [
        "activité physique", "activités physiques", "sport", "marche",
        "gym", "qi gong"
    ],
    "espaces publics et aménagement": [
        "aménagement", "aménagement urbain", "espace public",
        "espaces publics", "espace extérieur", "accessibilité",
        "voirie", "quartier"
    ],
    "services et accompagnement": [
        "service", "services", "accompagnement", "services à la personne",
        "aide à domicile", "offre de service"
    ],
    "politiques publiques": [
        "politique publique", "politiques publiques", "décentralisation",
        "collectivité", "institution", "financement"
    ],
    "environnement et développement durable": [
        "développement durable", "environnement", "climat", "climatologie",
        "écologie"
    ]
}

NATURE_KEYWORDS = {
    "atelier": ["atelier", "ateliers"],
    "formation": ["formation", "formations", "former"],
    "sensibilisation": ["sensibilisation", "sensibiliser", "campagne de sensibilisation"],
    "enquête": ["enquête", "questionnaire", "sondage", "étude"],
    "rapport": ["rapport", "diagnostic", "bilan"],
    "plaidoyer": ["plaidoyer", "revendication", "alerter", "interpeller"],
    "outil numérique": ["application", "plateforme", "site internet", "outil numérique", "carte interactive"],
    "événement": ["événement", "évènement", "journée", "forum", "salon", "rencontre", "conférence"],
    "accompagnement": ["accompagnement", "accompagner", "suivi personnalisé"],
    "dispositif": ["dispositif", "programme", "expérimentation"],
    "publication": ["publication", "guide", "livret", "brochure"],
    "offre de service": ["offre de service", "service proposé", "services proposés"],
    "groupe de parole": ["groupe de parole", "parole", "échange entre pairs"],
    "consultation citoyenne": ["consultation citoyenne", "concertation", "participation citoyenne"],
    "lieu / espace dédié": ["lieu dédié", "espace dédié", "tiers-lieu", "local dédié"],
    "projet d'aménagement": ["aménagement", "réaménagement", "urbanisme", "travaux"]
}

def find_text_file(json_file):
    relative_path = json_file.relative_to(JSON_DIR)
    txt_file = TEXT_DIR / relative_path.with_suffix(".txt")

    if txt_file.exists():
        return txt_file

    matches = list(TEXT_DIR.rglob(json_file.with_suffix(".txt").name))
    return matches[0] if matches else None


def detect_thematiques_by_rules(text):
    text_lower = text.lower()
    detected = []

    for theme, keywords in THEMATIQUE_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            detected.append(theme)

    if not detected:
        return ["autre"]

    return detected[:3]


def detect_nature_by_rules(text):
    text_lower = text.lower()

    for nature, keywords in NATURE_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            return nature

    return None


def build_prompt_nature(text):
    return f"""
Retourne uniquement un JSON strictement valide.
Aucun markdown. Aucun commentaire. Aucun texte avant ou après.

Tu dois choisir uniquement la valeur la plus adaptée pour "nature_initiative".

Valeurs autorisées :
{json.dumps(ALLOWED_NATURES, ensure_ascii=False, indent=2)}

Règles :
- Choisis une seule valeur.
- N'invente rien.
- Si plusieurs valeurs semblent possibles, choisis la nature principale.
- Si aucune valeur ne convient clairement, utilise "autre".

La sortie doit être exactement sous cette forme :
{{
  "nature_initiative": ""
}}

Texte :
{text}
""".strip()


def call_ollama(prompt):
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Tu réponds uniquement avec un JSON strictement valide."
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
            "num_predict": 100,
            "num_ctx": 4096
        }
    }

    response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=900)
    response.raise_for_status()
    return response.json()["message"]["content"]


def repair_json_text(text):
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


def extract_json(response_text):
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return json.loads(repair_json_text(response_text))


def normalize_nature(value):
    value = str(value).strip().lower()

    replacements = {
        "evenement": "événement",
        "évènement": "événement",
        "outil numerique": "outil numérique",
        "lieu espace dédié": "lieu / espace dédié",
        "lieu / espace dedie": "lieu / espace dédié",
        "projet d’aménagement": "projet d'aménagement",
        "projet d’amenagement": "projet d'aménagement",
        "amenagement": "projet d'aménagement",
        "aménagement": "projet d'aménagement"
    }

    value = replacements.get(value, value)

    if value in ALLOWED_NATURES:
        return value

    return "autre"


def update_file(json_file):
    txt_file = find_text_file(json_file)

    if txt_file is None:
        raise FileNotFoundError(f"Fichier texte introuvable pour {json_file.name}")

    with json_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    text = txt_file.read_text(encoding="utf-8", errors="ignore")[:MAX_CHARS]

    thematiques = detect_thematiques_by_rules(text)

    nature = detect_nature_by_rules(text)

    used_llm = False

    if nature is None:
        prompt = build_prompt_nature(text)
        response_text = call_ollama(prompt)
        parsed = extract_json(response_text)
        nature = normalize_nature(parsed.get("nature_initiative", ""))
        used_llm = True

    data["nature_initiative"] = normalize_nature(nature)
    data["thematique"] = thematiques

    with json_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return {
        "json": str(json_file),
        "txt": str(txt_file),
        "nature_initiative": data["nature_initiative"],
        "thematique": data["thematique"],
        "used_llm": used_llm
    }

def main():
    json_files = [
        file for file in JSON_DIR.rglob("*.json")
        if file.name not in {
            "errors_llm.json",
            "new_or_updated_vada_llm.json",
            "updated_nature_initiative.json",
            "updated_nature_thematique.json",
            "errors_nature_thematique.json",
            "updated_hybrid_nature_thematique.json",
            "errors_hybrid_nature_thematique.json"
        }
    ]

    print(f"{len(json_files)} fichier(s) JSON trouvé(s)")
    print(f"Modèle : {MODEL}")
    print(f"MAX_CHARS : {MAX_CHARS}")
    print(f"Workers : {MAX_WORKERS}")
    print("Mode : thematique par règles + nature_initiative par règles puis LLM si nécessaire")

    updated = []
    errors = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(update_file, json_file): json_file
            for json_file in json_files
        }

        for future in tqdm(as_completed(futures), total=len(futures), desc="Mise à jour", unit="fichier"):
            json_file = futures[future]

            try:
                result = future.result()
                updated.append(result)

                llm_status = "LLM" if result["used_llm"] else "règles"

                tqdm.write(
                    f"OK : {json_file.name} -> "
                    f"{result['nature_initiative']} ({llm_status}) | "
                    f"{', '.join(result['thematique'])}"
                )

            except Exception as e:
                errors.append({
                    "fichier": str(json_file),
                    "erreur": str(e)
                })
                tqdm.write(f"ERREUR avec {json_file.name}: {e}")

    with (JSON_DIR / "updated_hybrid_nature_thematique.json").open("w", encoding="utf-8") as f:
        json.dump(updated, f, indent=4, ensure_ascii=False)

    with (JSON_DIR / "errors_hybrid_nature_thematique.json").open("w", encoding="utf-8") as f:
        json.dump(errors, f, indent=4, ensure_ascii=False)

    nb_llm = sum(1 for item in updated if item["used_llm"])
    nb_rules = len(updated) - nb_llm

    print("\nTerminé")
    print(f"Fichiers mis à jour : {len(updated)}")
    print(f"Traités par règles uniquement : {nb_rules}")
    print(f"Traités avec LLM pour nature_initiative : {nb_llm}")
    print(f"Erreurs : {len(errors)}")
    print(f"Rapport : {JSON_DIR / 'updated_hybrid_nature_thematique.json'}")
    print(f"Rapport erreurs : {JSON_DIR / 'errors_hybrid_nature_thematique.json'}")


if __name__ == "__main__":
    main()