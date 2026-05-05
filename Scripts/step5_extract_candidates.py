from pathlib import Path
import json
import re

PROJECT_ROOT = Path(r"C:\Users\PC\Desktop\Project_Internship\Index_Insight")

INPUT_DIR = PROJECT_ROOT / "Entities_Database"
OUTPUT_DIR = PROJECT_ROOT / "Candidates_Database"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

KEYWORDS = {
    "public_vise": [
        "public", "public visé", "bénéficiaires", "personnes concernées",
        "personnes âgées", "seniors", "aidants", "habitants", "usagers",
        "personnes en perte d’autonomie", "personnes en perte d'autonomie",
        "professionnels", "familles", "résidents"
    ],
    "porteur": [
        "porteur", "porté par", "portée par", "structure porteuse",
        "piloté par", "pilotée par", "mis en place par", "mise en place par",
        "à l’initiative de", "à l'initiative de", "organisé par", "coordonné par",
        "animé par"
    ],
    "territoire": [
        "territoire", "localisation", "lieu", "commune", "ville",
        "département", "région", "quartier", "métropole", "intercommunalité"
    ],
    "description": [
        "description", "présentation", "résumé", "descriptif",
        "projet", "initiative", "action", "dispositif", "expérimentation"
    ],
    "contexte": [
        "contexte", "diagnostic", "constat", "situation initiale",
        "dans un contexte", "face à", "en raison de"
    ],
    "problematique": [
        "problématique", "problematique", "enjeu", "enjeux",
        "besoin", "difficulté", "frein", "problème", "isolement"
    ],
    "solution": [
        "solution", "réponse", "action mise en place", "mise en place",
        "déploiement", "accompagnement", "propose", "permet de"
    ],
    "objectifs": [
        "objectif", "objectifs", "vise à", "a pour but", "afin de",
        "permettre de", "favoriser", "développer", "améliorer", "renforcer"
    ]
}

MAX_CANDIDATES = 8

def normalize_text(text: str) -> str:
    text = text.replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def score_sentence(sentence: str, keywords: list[str]) -> int:
    sentence_norm = normalize_text(sentence).lower()
    score = 0

    for keyword in keywords:
        keyword_norm = normalize_text(keyword).lower()
        if keyword_norm in sentence_norm:
            score += 2

    if 60 <= len(sentence) <= 400:
        score += 1

    if ":" in sentence:
        score += 1

    return score

def get_candidates(sentences: list[str], keywords: list[str], max_candidates: int = MAX_CANDIDATES) -> list[dict]:
    candidates = []

    for sentence in sentences:
        score = score_sentence(sentence, keywords)

        if score > 0:
            candidates.append({
                "texte": sentence,
                "score": score
            })

    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

    unique = []
    seen = set()

    for candidate in candidates:
        key = normalize_text(candidate["texte"]).lower()

        if key not in seen:
            unique.append(candidate)
            seen.add(key)

        if len(unique) >= max_candidates:
            break

    return unique

def add_section_candidates(data: dict, candidates: dict) -> dict:
    sections = data.get("sections_detectees", {})

    mapping = {
        "public_vise": "public_vise_candidates",
        "porteur_initiative": "porteur_candidates",
        "territoire": "territoire_candidates",
        "description": "description_candidates",
        "contexte": "contexte_candidates",
        "problematique": "problematique_candidates",
        "solution_envisagee": "solution_candidates",
        "objectifs": "objectifs_candidates"
    }

    for section_name, candidate_name in mapping.items():
        value = sections.get(section_name, "")

        if value:
            candidates.setdefault(candidate_name, [])
            candidates[candidate_name].insert(0, {
                "texte": value,
                "score": 10,
                "source": "section_detectee"
            })

    return candidates

def process_file(json_path: Path) -> dict:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    sentences = data.get("phrases", [])

    candidates = {
        "public_vise_candidates": get_candidates(sentences, KEYWORDS["public_vise"]),
        "porteur_candidates": get_candidates(sentences, KEYWORDS["porteur"]),
        "territoire_candidates": get_candidates(sentences, KEYWORDS["territoire"]),
        "description_candidates": get_candidates(sentences, KEYWORDS["description"]),
        "contexte_candidates": get_candidates(sentences, KEYWORDS["contexte"]),
        "problematique_candidates": get_candidates(sentences, KEYWORDS["problematique"]),
        "solution_candidates": get_candidates(sentences, KEYWORDS["solution"]),
        "objectifs_candidates": get_candidates(sentences, KEYWORDS["objectifs"])
    }

    candidates = add_section_candidates(data, candidates)

    data["phrases_candidates"] = candidates

    if "stats" not in data:
        data["stats"] = {}

    for key, value in candidates.items():
        data["stats"][f"nombre_{key}"] = len(value)

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

            print(f"Candidats extraits : {relative_path}")

        except Exception as e:
            print(f"Erreur avec {json_file} : {e}")

    print("\nExtraction des phrases candidates terminée.")
    print(f"Dossier de sortie : {OUTPUT_DIR}")

if __name__ == "__main__":
    main()