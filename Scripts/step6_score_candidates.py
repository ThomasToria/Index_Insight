from pathlib import Path
import json

PROJECT_ROOT = Path(r"C:\Users\PC\Desktop\Project_Internship\Index_Insight")

INPUT_DIR = PROJECT_ROOT / "Candidates_Database"
OUTPUT_DIR = PROJECT_ROOT / "Scored_Database"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FIELD_MAPPING = {
    "public_vise": "public_vise_candidates",
    "porteur_initiative": "porteur_candidates",
    "territoire": "territoire_candidates",
    "description": "description_candidates",
    "contexte": "contexte_candidates",
    "problematique": "problematique_candidates",
    "solution_envisagee": "solution_candidates",
    "objectifs": "objectifs_candidates"
}

def confidence_from_score(score: int) -> float:
    if score >= 10:
        return 0.95
    if score >= 7:
        return 0.80
    if score >= 5:
        return 0.65
    if score >= 3:
        return 0.45
    if score >= 1:
        return 0.25
    return 0.0

def select_best_candidate(candidates: list[dict]) -> dict:
    if not candidates:
        return {
            "valeur": "",
            "score": 0,
            "confiance": 0.0,
            "source": ""
        }

    best = sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)[0]

    score = best.get("score", 0)

    return {
        "valeur": best.get("texte", ""),
        "score": score,
        "confiance": confidence_from_score(score),
        "source": best.get("source", "phrase_candidate")
    }

def extract_title(data: dict) -> dict:
    lines = data.get("lignes", [])

    for line in lines:
        if 5 <= len(line) <= 180:
            return {
                "valeur": line,
                "score": 8,
                "confiance": 0.80,
                "source": "premiere_ligne"
            }

    return {
        "valeur": "",
        "score": 0,
        "confiance": 0.0,
        "source": ""
    }

def extract_dates(data: dict) -> dict:
    dates = data.get("entites_candidates", {}).get("dates_candidates", [])

    if dates:
        return {
            "valeur": dates,
            "score": 7,
            "confiance": 0.80,
            "source": "regex_dates"
        }

    return {
        "valeur": [],
        "score": 0,
        "confiance": 0.0,
        "source": ""
    }

def extract_thematiques(data: dict) -> dict:
    phrases = " ".join(data.get("phrases", [])).lower()

    thematiques_keywords = {
        "autonomie": ["autonomie", "perte d’autonomie", "perte d'autonomie", "dépendance"],
        "vieillissement": ["vieillissement", "personnes âgées", "senior", "seniors"],
        "habitat": ["habitat", "logement", "domicile", "résidence"],
        "mobilité": ["mobilité", "transport", "déplacement"],
        "santé": ["santé", "soin", "soins", "prévention"],
        "lien social": ["isolement", "lien social", "solidarité", "convivialité"],
        "numérique": ["numérique", "application", "plateforme", "outil digital"],
        "aidants": ["aidant", "aidants", "proche aidant"],
        "inclusion": ["inclusion", "accessibilité", "handicap"]
    }

    results = []

    for thematique, keywords in thematiques_keywords.items():
        if any(keyword in phrases for keyword in keywords):
            results.append(thematique)

    score = min(len(results) * 2, 8)

    return {
        "valeur": results,
        "score": score,
        "confiance": confidence_from_score(score),
        "source": "keywords_thematiques"
    }

def extract_echelle(data: dict) -> dict:
    phrases = " ".join(data.get("phrases", [])).lower()

    echelles_keywords = {
        "quartier": ["quartier", "arrondissement", "îlot", "ilot"],
        "communale": ["commune", "ville", "municipalité", "mairie", "ccas"],
        "intercommunale": ["intercommunalité", "communauté de communes", "métropole", "agglomération"],
        "départementale": ["département", "conseil départemental"],
        "régionale": ["région", "conseil régional"],
        "nationale": ["national", "nationale", "france entière", "ministère"],
        "internationale": ["international", "internationale", "europe", "union européenne"]
    }

    results = []

    for echelle, keywords in echelles_keywords.items():
        if any(keyword in phrases for keyword in keywords):
            results.append(echelle)

    score = min(len(results) * 2, 8)

    return {
        "valeur": results,
        "score": score,
        "confiance": confidence_from_score(score),
        "source": "keywords_echelles"
    }

def detect_source_site(json_path: Path) -> str:
    parts = json_path.parts

    source_mapping = {
        "Cnav_database": "CNAV",
        "cnsa_database": "CNSA",
        "FdF_database": "Fondation de France",
        "Fiches_actions_database": "Fiches actions",
        "Hcfea_database": "HCFEA",
        "iresp_autonomie_database": "IRESP Autonomie",
        "Vada_database": "VADA"
    }

    for part in parts:
        if part in source_mapping:
            return source_mapping[part]

    return ""

def build_scored_fields(data: dict, json_path: Path) -> dict:
    candidates = data.get("phrases_candidates", {})

    scored = {}

    scored["titre"] = extract_title(data)
    scored["date"] = extract_dates(data)
    scored["thematique"] = extract_thematiques(data)
    scored["echelle"] = extract_echelle(data)

    for field_name, candidate_key in FIELD_MAPPING.items():
        scored[field_name] = select_best_candidate(candidates.get(candidate_key, []))

    scored["source_site"] = {
        "valeur": detect_source_site(json_path),
        "score": 10,
        "confiance": 0.95,
        "source": "nom_dossier"
    }

    return scored

def process_file(json_path: Path) -> dict:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data["champs_scores"] = build_scored_fields(data, json_path)

    return data

def main():
    json_files = list(INPUT_DIR.rglob("*.json"))

    if not json_files:
        print(f"Aucun fichier .json trouvé dans : {INPUT_DIR}")
        return

    print(f"{len(json_files)} fichier(s) trouvé(s).")

    for json_file in json_files:
        try:
            scored_data = process_file(json_file)

            relative_path = json_file.relative_to(INPUT_DIR)
            output_file = OUTPUT_DIR / relative_path
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with output_file.open("w", encoding="utf-8") as f:
                json.dump(scored_data, f, ensure_ascii=False, indent=4)

            print(f"Scoré : {relative_path}")

        except Exception as e:
            print(f"Erreur avec {json_file} : {e}")

    print("\nScoring terminé.")
    print(f"Dossier de sortie : {OUTPUT_DIR}")

if __name__ == "__main__":
    main()