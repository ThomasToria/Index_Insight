"""Normalise les thèmes et les natures d'initiative des fiches JSON.

Le script conserve toujours les champs LLM d'origine (``thematique`` et
``nature_initiative``) et ajoute deux champs de post-traitement :

* ``thematique_normalisee`` : liste de catégories contrôlées ;
* ``nature_initiative_normalisee`` : catégorie contrôlée unique.

Il n'appelle pas de modèle : la normalisation est déterministe, traçable et
reproductible. Les valeurs ambiguës sont orientées vers ``autre / à revoir``
plutôt que d'être attribuées arbitrairement à une catégorie. Des rapports CSV
permettent de les contrôler manuellement.

Exemples :
    py .\\Scripts\\normaliser_taxonomie.py --dry-run
    py .\\Scripts\\normaliser_taxonomie.py --apply
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_DIR = PROJECT_ROOT / "LLM_Tagged_Database"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "outputs_graphs" / "normalisation_taxonomie"
TAXONOMY_VERSION = "v1.0"


# Les libellés sont en français car ils décrivent un corpus, un prompt et un
# projet destinés à des utilisateurs francophones.
THEMES_CONTROLES = [
    "autonomie et avancée en âge",
    "santé et prévention",
    "aidants, handicap et vulnérabilités",
    "lien social et lutte contre l'isolement",
    "intergénérationnel",
    "mobilité et accessibilité",
    "habitat et logement",
    "numérique et accès à l'information",
    "participation citoyenne et gouvernance",
    "culture et loisirs",
    "activité physique et sport",
    "espaces publics et aménagement",
    "services et accompagnement",
    "politiques publiques et recherche",
    "environnement et développement durable",
    "autre / à revoir",
]

NATURES_CONTROLEES = [
    "atelier",
    "formation",
    "sensibilisation",
    "enquête ou étude",
    "rapport ou publication",
    "plaidoyer",
    "outil numérique",
    "événement",
    "accompagnement",
    "dispositif ou programme",
    "offre de service",
    "groupe de parole",
    "consultation citoyenne",
    "lieu ou espace dédié",
    "projet d'aménagement",
    "autre / à revoir",
    "non renseigné",
]


# Correspondances qui nécessitent une décision éditoriale explicite. Elles sont
# appliquées avant les règles par mots-clés afin de documenter les cas composés.
THEME_CORRESPONDANCES_EXACTES = {
    "activite physique": ["activité physique et sport"],
    "activites loisirs": ["culture et loisirs"],
    "activite physique et sport": ["activité physique et sport"],
    "aide aux aidants": ["aidants, handicap et vulnérabilités"],
    "aidant": ["aidants, handicap et vulnérabilités"],
    "aidants": ["aidants, handicap et vulnérabilités"],
    "aidants familiaux": ["aidants, handicap et vulnérabilités"],
    "autisme": ["aidants, handicap et vulnérabilités"],
    "autonomie": ["autonomie et avancée en âge"],
    "autonomie des personnes agees": ["autonomie et avancée en âge"],
    "autonomie et grand age": ["autonomie et avancée en âge"],
    "autonomie grand age et handicap": [
        "autonomie et avancée en âge",
        "aidants, handicap et vulnérabilités",
    ],
    "bien etre": ["santé et prévention"],
    "communication sociale": ["lien social et lutte contre l'isolement"],
    "culture": ["culture et loisirs"],
    "culture et loisirs": ["culture et loisirs"],
    "developpement durable": ["environnement et développement durable"],
    "enfants": ["intergénérationnel"],
    "epidemiologie": ["santé et prévention"],
    "espaces publics et amenagement": ["espaces publics et aménagement"],
    "famille": ["aidants, handicap et vulnérabilités"],
    "familles": ["aidants, handicap et vulnérabilités"],
    "fin de vie": ["santé et prévention"],
    "grand age": ["autonomie et avancée en âge"],
    "grand age et handicap": [
        "autonomie et avancée en âge",
        "aidants, handicap et vulnérabilités",
    ],
    "handicap": ["aidants, handicap et vulnérabilités"],
    "handicap et aidants": ["aidants, handicap et vulnérabilités"],
    "habitat": ["habitat et logement"],
    "habitat et logement": ["habitat et logement"],
    "inclusion": ["lien social et lutte contre l'isolement"],
    "inclusion sociale": ["lien social et lutte contre l'isolement"],
    "intergenerationnel": ["intergénérationnel"],
    "isolement": ["lien social et lutte contre l'isolement"],
    "isolation": ["lien social et lutte contre l'isolement"],
    "lien social": ["lien social et lutte contre l'isolement"],
    "lien social et isolement": ["lien social et lutte contre l'isolement"],
    "liens sociaux": ["lien social et lutte contre l'isolement"],
    "logement": ["habitat et logement"],
    "maladie d alzheimer": ["santé et prévention"],
    "maladies neurodegeneratives": ["santé et prévention"],
    "mobilite": ["mobilité et accessibilité"],
    "mobilite et isolation": [
        "mobilité et accessibilité",
        "lien social et lutte contre l'isolement",
    ],
    "mobilite et transport": ["mobilité et accessibilité"],
    "mobilites": ["mobilité et accessibilité"],
    "numerique": ["numérique et accès à l'information"],
    "nutrition": ["santé et prévention"],
    "pandemie de covid 19": ["santé et prévention"],
    "participation": ["participation citoyenne et gouvernance"],
    "participation citoyenne": ["participation citoyenne et gouvernance"],
    "participation sociale": ["participation citoyenne et gouvernance"],
    "personnes agees": ["autonomie et avancée en âge"],
    "politiques publiques": ["politiques publiques et recherche"],
    "politique": ["politiques publiques et recherche"],
    "professionnels de sante": ["santé et prévention"],
    "prevention": ["santé et prévention"],
    "recherche": ["politiques publiques et recherche"],
    "retraite": ["autonomie et avancée en âge"],
    "retraites": ["autonomie et avancée en âge"],
    "senior": ["autonomie et avancée en âge"],
    "seniors": ["autonomie et avancée en âge"],
    "sante": ["santé et prévention"],
    "sante et bien etre": ["santé et prévention"],
    "sante et prevention": ["santé et prévention"],
    "sante mentale": ["santé et prévention"],
    "sante mentale des personnes agees": ["santé et prévention"],
    "sante publique": ["santé et prévention"],
    "services et accompagnement": ["services et accompagnement"],
    "services interventions et politiques favorables a la sante": [
        "services et accompagnement",
        "santé et prévention",
    ],
    "services sociaux": ["services et accompagnement"],
    "social": ["lien social et lutte contre l'isolement"],
    "solidarite": ["lien social et lutte contre l'isolement"],
    "technologie": ["numérique et accès à l'information"],
    "transport": ["mobilité et accessibilité"],
    "urbanisme": ["espaces publics et aménagement"],
    "vieillissement": ["autonomie et avancée en âge"],
    "vieillissement actif": ["autonomie et avancée en âge"],
}

NATURE_CORRESPONDANCES = {
    "accompagnement": "accompagnement",
    "atelier": "atelier",
    "consultation citoyenne": "consultation citoyenne",
    "dispositif": "dispositif ou programme",
    "enquete": "enquête ou étude",
    "etude": "enquête ou étude",
    "evenement": "événement",
    "formation": "formation",
    "groupe de parole": "groupe de parole",
    "lieu espace dedie": "lieu ou espace dédié",
    "offre de service": "offre de service",
    "plaidoyer": "plaidoyer",
    "projet d amenagement": "projet d'aménagement",
    "projet amenagement": "projet d'aménagement",
    "publication": "rapport ou publication",
    "rapport": "rapport ou publication",
    "sensibilisation": "sensibilisation",
    "outil numerique": "outil numérique",
}


def simplifier(texte: Any) -> str:
    """Uniformise accents, ponctuation et espaces pour les correspondances."""
    texte = str(texte or "").strip().lower()
    texte = unicodedata.normalize("NFKD", texte)
    texte = "".join(caractere for caractere in texte if not unicodedata.combining(caractere))
    texte = texte.replace("œ", "oe").replace("æ", "ae")
    texte = re.sub(r"[^a-z0-9]+", " ", texte)
    return re.sub(r"\s+", " ", texte).strip()


def extraire_valeurs(valeur: Any) -> list[str]:
    """Aplatit une valeur JSON tout en ignorant les valeurs vides."""
    if valeur is None:
        return []
    if isinstance(valeur, list):
        resultat: list[str] = []
        for element in valeur:
            resultat.extend(extraire_valeurs(element))
        return resultat
    if isinstance(valeur, str) and valeur.strip():
        return [valeur.strip()]
    return []


def normaliser_theme(valeur: str) -> list[str]:
    """Associe un thème libre à une ou plusieurs catégories contrôlées."""
    cle = simplifier(valeur)
    if not cle:
        return ["autre / à revoir"]

    correspondance = THEME_CORRESPONDANCES_EXACTES.get(cle)
    if correspondance:
        return correspondance

    # Les règles suivantes ne concernent que les libellés, jamais le texte intégral
    # des documents. Elles restent donc lisibles et simples à contrôler.
    regles = [
        ("aidants, handicap et vulnérabilités", ("aidant", "handicap", "vulnerabilit", "autisme")),
        ("intergénérationnel", ("intergeneration",)),
        ("mobilité et accessibilité", ("mobilite", "transport", "deplacement")),
        ("habitat et logement", ("habitat", "logement", "domicile")),
        ("numérique et accès à l'information", ("numerique", "digital", "technologie")),
        ("participation citoyenne et gouvernance", ("participation", "citoyen", "gouvernance")),
        ("activité physique et sport", ("sport", "activite physique")),
        ("culture et loisirs", ("culture", "loisir", "artist", "patrimoine")),
        ("espaces publics et aménagement", ("amenagement", "urbanisme", "espace public")),
        ("services et accompagnement", ("service", "accompagnement")),
        ("politiques publiques et recherche", ("politique publique", "recherche", "evaluation")),
        ("environnement et développement durable", ("environnement", "developpement durable", "ecologie")),
        ("lien social et lutte contre l'isolement", ("lien social", "isolement", "inclusion", "solidarite")),
        ("santé et prévention", ("sante", "prevention", "soin", "maladie")),
        ("autonomie et avancée en âge", ("autonomie", "vieillissement", "grand age", "senior", "aine", "retraite")),
    ]
    categories = [categorie for categorie, motifs in regles if any(motif in cle for motif in motifs)]
    return categories or ["autre / à revoir"]


def normaliser_nature(valeur: Any) -> str:
    """Associe la nature libre à une catégorie contrôlée unique."""
    valeurs = extraire_valeurs(valeur)
    if not valeurs:
        return "non renseigné"

    cle = simplifier(valeurs[0])
    if cle in NATURE_CORRESPONDANCES:
        return NATURE_CORRESPONDANCES[cle]

    # Une nature est volontairement plus stricte qu'un thème : en cas de doute,
    # elle doit être revue plutôt que rapprochée d'une catégorie approximative.
    return "autre / à revoir"


def est_fiche_json(donnees: Any) -> bool:
    """Écarte les rapports JSON techniques présents dans le même répertoire."""
    if not isinstance(donnees, dict):
        return False
    champs = set(donnees)
    return bool({"titre", "source_site", "thematique", "nature_initiative"} & champs)


def lire_fiches(repertoire: Path) -> tuple[list[tuple[Path, dict[str, Any]]], list[dict[str, str]]]:
    fiches: list[tuple[Path, dict[str, Any]]] = []
    erreurs: list[dict[str, str]] = []
    for chemin in sorted(repertoire.rglob("*.json")):
        try:
            with chemin.open("r", encoding="utf-8") as fichier:
                donnees = json.load(fichier)
            if est_fiche_json(donnees):
                fiches.append((chemin, donnees))
        except (OSError, json.JSONDecodeError) as erreur:
            erreurs.append({"fichier": str(chemin), "erreur": str(erreur)})
    return fiches, erreurs


def ecrire_csv(chemin: Path, lignes: list[dict[str, Any]], champs: list[str]) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", encoding="utf-8-sig", newline="") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=champs, delimiter=";")
        writer.writeheader()
        writer.writerows(lignes)


def creer_rapports(
    fiches: list[tuple[Path, dict[str, Any]]],
    erreurs: list[dict[str, str]],
    repertoire_rapports: Path,
    mode: str,
) -> None:
    themes_bruts: Counter[str] = Counter()
    themes_a_revoir: Counter[str] = Counter()
    themes_normalises: Counter[str] = Counter()
    natures_brutes: Counter[str] = Counter()
    natures_a_revoir: Counter[str] = Counter()
    natures_normalisees: Counter[str] = Counter()

    for _, donnees in fiches:
        for theme in extraire_valeurs(donnees.get("thematique")):
            themes_bruts[theme] += 1
            categories = normaliser_theme(theme)
            themes_normalises.update(categories)
            if "autre / à revoir" in categories:
                themes_a_revoir[theme] += 1

        nature_brute = " | ".join(extraire_valeurs(donnees.get("nature_initiative"))) or "(vide)"
        natures_brutes[nature_brute] += 1
        nature_normalisee = normaliser_nature(donnees.get("nature_initiative"))
        natures_normalisees[nature_normalisee] += 1
        if nature_normalisee == "autre / à revoir":
            natures_a_revoir[nature_brute] += 1

    resume = [
        {"indicateur": "version_taxonomie", "valeur": TAXONOMY_VERSION},
        {"indicateur": "mode", "valeur": mode},
        {"indicateur": "fiches_JSON_traitees", "valeur": len(fiches)},
        {"indicateur": "fichiers_JSON_en_erreur", "valeur": len(erreurs)},
        {"indicateur": "valeurs_thematiques_brutes_distinctes", "valeur": len(themes_bruts)},
        {"indicateur": "valeurs_natures_brutes_distinctes", "valeur": len(natures_brutes)},
        {"indicateur": "occurrences_thematiques_a_revoir", "valeur": sum(themes_a_revoir.values())},
        {"indicateur": "occurrences_natures_a_revoir", "valeur": sum(natures_a_revoir.values())},
    ]
    ecrire_csv(repertoire_rapports / "resume_normalisation.csv", resume, ["indicateur", "valeur"])

    lignes_themes = [
        {"thematique_normalisee": categorie, "occurrences": occurrences}
        for categorie, occurrences in themes_normalises.most_common()
    ]
    ecrire_csv(
        repertoire_rapports / "distribution_thematiques_normalisees.csv",
        lignes_themes,
        ["thematique_normalisee", "occurrences"],
    )

    lignes_natures = [
        {"nature_initiative_normalisee": categorie, "occurrences": occurrences}
        for categorie, occurrences in natures_normalisees.most_common()
    ]
    ecrire_csv(
        repertoire_rapports / "distribution_natures_normalisees.csv",
        lignes_natures,
        ["nature_initiative_normalisee", "occurrences"],
    )

    lignes_a_revoir = [
        {"champ": "thematique", "valeur_brute": valeur, "occurrences": occurrences}
        for valeur, occurrences in themes_a_revoir.most_common()
    ] + [
        {"champ": "nature_initiative", "valeur_brute": valeur, "occurrences": occurrences}
        for valeur, occurrences in natures_a_revoir.most_common()
    ]
    ecrire_csv(
        repertoire_rapports / "valeurs_a_revoir.csv",
        lignes_a_revoir,
        ["champ", "valeur_brute", "occurrences"],
    )

    if erreurs:
        ecrire_csv(repertoire_rapports / "erreurs_lecture_json.csv", erreurs, ["fichier", "erreur"])


def appliquer_normalisation(fiches: list[tuple[Path, dict[str, Any]]]) -> int:
    modifiees = 0
    for chemin, donnees in fiches:
        themes_normalises: list[str] = []
        for theme in extraire_valeurs(donnees.get("thematique")):
            for categorie in normaliser_theme(theme):
                if categorie not in themes_normalises:
                    themes_normalises.append(categorie)
        if not themes_normalises:
            themes_normalises = ["autre / à revoir"]

        nouveau = {
            "thematique_normalisee": themes_normalises,
            "nature_initiative_normalisee": normaliser_nature(donnees.get("nature_initiative")),
            "version_taxonomie": TAXONOMY_VERSION,
        }
        if any(donnees.get(cle) != valeur for cle, valeur in nouveau.items()):
            donnees.update(nouveau)
            with chemin.open("w", encoding="utf-8") as fichier:
                json.dump(donnees, fichier, ensure_ascii=False, indent=2)
                fichier.write("\n")
            modifiees += 1
    return modifiees


def analyser_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalise les thèmes et natures d'initiative.")
    groupe = parser.add_mutually_exclusive_group(required=True)
    groupe.add_argument("--dry-run", action="store_true", help="Produit les rapports sans modifier les JSON.")
    groupe.add_argument("--apply", action="store_true", help="Ajoute les champs normalisés dans les JSON.")
    parser.add_argument("--json-dir", type=Path, default=DEFAULT_JSON_DIR, help="Répertoire des fiches JSON.")
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR, help="Répertoire de sortie des rapports.")
    return parser.parse_args()


def main() -> None:
    args = analyser_arguments()
    fiches, erreurs = lire_fiches(args.json_dir)
    mode = "dry-run" if args.dry_run else "apply"
    creer_rapports(fiches, erreurs, args.report_dir, mode)

    modifiees = appliquer_normalisation(fiches) if args.apply else 0
    print(f"Mode : {mode}")
    print(f"Fiches JSON traitées : {len(fiches)}")
    print(f"Fichiers JSON en erreur : {len(erreurs)}")
    print(f"Fiches modifiées : {modifiees}")
    print(f"Rapports : {args.report_dir}")


if __name__ == "__main__":
    main()
