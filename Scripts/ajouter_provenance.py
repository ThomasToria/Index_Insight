"""Ajoute des métadonnées de provenance aux fiches JSON du corpus.

Les informations sont obtenues à partir des index et des textes collectés, sans
recourir au LLM. Les champs ajoutés sont :

* ``source_url`` : URL exacte de la page ou du PDF, lorsqu'elle est disponible ;
* ``original_title`` : titre conservé dans l'index ou la source collectée ;
* ``collection_date`` : date de collecte au format ISO, lorsqu'elle est connue ;
* ``source_site`` : identifiant harmonisé de la collection source.

Les index historiques ne contiennent pas de date de collecte fiable. Le script
laisse donc ``collection_date`` vide au lieu d'utiliser une date de modification
de fichier, qui ne représenterait pas la date réelle de collecte.

Exemples :
    .\\venv\\Scripts\\python.exe .\\Scripts\\ajouter_provenance.py --dry-run
    .\\venv\\Scripts\\python.exe .\\Scripts\\ajouter_provenance.py --apply
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LLM_ROOT = PROJECT_ROOT / "LLM_Tagged_Database"
REPORT_DIR = PROJECT_ROOT / "Evaluation" / "provenance"
CNAV_PDF_URL = (
    "https://www.lassuranceretraite.fr/portail-info/files/live/sites/pub/files/"
    "PDF/pepites-assurance-retraite-pour-bien-vieillir-2023.pdf"
)

SOURCE_SITES = {
    "cnav_database": "CNAV",
    "fdf_database": "Fondation de France",
    "fiches_actions_database": "SIAGE",
    "hcfea_database": "HCFEA",
    "iresp_autonomie_database": "IReSP Autonomie",
    "vada_database": "RFVAA",
}


def cle_fichier(value: str) -> str:
    """Produit une clé stable à partir d'un nom de fichier ou d'un chemin."""
    stem = Path(value).stem
    stem = unicodedata.normalize("NFKD", stem)
    stem = "".join(char for char in stem if not unicodedata.combining(char))
    stem = stem.lower().replace("œ", "oe").replace("æ", "ae")
    return re.sub(r"[^a-z0-9]+", "", stem)


def lire_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file, delimiter=delimiter))


def construire_index_simple(
    rows: list[dict[str, str]],
    filename_column: str,
    title_column: str,
    url_column: str | None = None,
    default_url: str = "",
) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for row in rows:
        filename = row.get(filename_column, "")
        if not filename:
            continue
        index[cle_fichier(filename)] = {
            "original_title": row.get(title_column, "").strip(),
            "source_url": row.get(url_column, "").strip() if url_column else default_url,
            "collection_date": "",
        }
    return index


def index_cnav() -> dict[str, dict[str, str]]:
    rows = lire_csv(PROJECT_ROOT / "temp" / "cnav_scrapping" / "index_articles.csv")
    return construire_index_simple(
        rows,
        filename_column="txt_file",
        title_column="title",
        default_url=CNAV_PDF_URL,
    )


def index_hcfea() -> dict[str, dict[str, str]]:
    rows = lire_csv(PROJECT_ROOT / "temp" / "hcfea_scraping" / "index_hcfea_conseil_age.csv")
    return construire_index_simple(rows, "txt_file", "title", "article_url")


def index_iresp() -> dict[str, dict[str, str]]:
    rows = lire_csv(PROJECT_ROOT / "Scripts" / "iresp_autonomie_report.csv", delimiter=";")
    accepted = [row for row in rows if row.get("status", "").strip().lower() == "accepted"]
    return construire_index_simple(accepted, "path", "title", "url")


def index_vada() -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for name in ("index_vada.csv", "index_vada_21_40.csv", "index_vada_41_60.csv", "index_vada_61_80.csv"):
        rows = lire_csv(PROJECT_ROOT / name)
        index.update(construire_index_simple(rows, "txt_file", "title", "pdf_url"))
    return index


def index_fiches_siage() -> dict[str, dict[str, str]]:
    rows = lire_csv(PROJECT_ROOT / "index_fiches.csv")
    return construire_index_simple(rows, "txt_file", "source_file")


def index_fondation_de_france() -> dict[str, dict[str, str]]:
    """Extrait titre et URL archivés dans les fichiers bruts Fondation de France."""
    index: dict[str, dict[str, str]] = {}
    directory = PROJECT_ROOT / "Database" / "FdF_database"
    for path in directory.glob("*.txt"):
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        title = next((line.strip() for line in lines if line.strip()), "")
        url = next((line.strip() for line in lines if line.strip().startswith("http")), "")
        index[cle_fichier(path.name)] = {
            "original_title": title,
            "source_url": url,
            "collection_date": "",
        }
    return index


def construire_indexes() -> dict[str, dict[str, dict[str, str]]]:
    return {
        "cnav_database": index_cnav(),
        "fdf_database": index_fondation_de_france(),
        "fiches_actions_database": index_fiches_siage(),
        "hcfea_database": index_hcfea(),
        "iresp_autonomie_database": index_iresp(),
        "vada_database": index_vada(),
    }


def est_fiche(donnees: Any) -> bool:
    return isinstance(donnees, dict) and bool(
        {"titre", "source_site", "thematique", "nature_initiative"} & set(donnees)
    )


def trouver_provenance(
    path: Path,
    data: dict[str, Any],
    indexes: dict[str, dict[str, dict[str, str]]],
) -> tuple[str, dict[str, str] | None, str]:
    # Les noms de répertoires historiques ne suivent pas tous la même casse
    # (par exemple Cnav_database et iresp_autonomie_database).
    source_directory = path.parent.name.lower()
    index = indexes.get(source_directory, {})
    candidates = [
        str(data.get("nom_fichier", "")),
        str(data.get("fichier_source", "")),
        path.stem,
        str(data.get("titre", "")),
    ]
    normalized_candidates = [cle_fichier(candidate) for candidate in candidates if candidate]

    # Correspondance exacte : cas normal lorsque le nom de fichier de l'index a
    # été conservé lors des étapes de nettoyage et d'extraction.
    for candidate in normalized_candidates:
        record = index.get(candidate)
        if record:
            return source_directory, record, "exacte"

    # Certaines étapes historiques ont tronqué des noms longs. Une correspondance
    # par préfixe reste vérifiable et est explicitement signalée dans le rapport.
    prefix_matches: list[tuple[int, str]] = []
    for candidate in normalized_candidates:
        for key in index:
            if len(candidate) >= 12 and (key.startswith(candidate) or candidate.startswith(key)):
                prefix_matches.append((min(len(candidate), len(key)), key))
    if prefix_matches:
        _, best_key = max(prefix_matches)
        return source_directory, index[best_key], "préfixe"

    # Dernier recours contrôlé : titre ou nom fortement similaire. Le seuil élevé
    # évite de relier automatiquement deux initiatives distinctes mais proches.
    fuzzy_matches: list[tuple[float, str]] = []
    for candidate in normalized_candidates:
        if len(candidate) < 12:
            continue
        for key in index:
            score = difflib.SequenceMatcher(a=candidate, b=key).ratio()
            if score >= 0.88:
                fuzzy_matches.append((score, key))
    if fuzzy_matches:
        _, best_key = max(fuzzy_matches)
        return source_directory, index[best_key], "similarité élevée"

    return source_directory, None, "introuvable"


def ecrire_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def traiter(apply: bool) -> None:
    indexes = construire_indexes()
    rows: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    changed = 0

    for path in sorted(LLM_ROOT.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            unmatched.append({"fichier": str(path), "source": "", "raison": f"JSON illisible : {error}"})
            continue
        if not est_fiche(data):
            continue

        source_directory, provenance, matching_method = trouver_provenance(path, data, indexes)
        source_site = SOURCE_SITES.get(source_directory, str(data.get("source_site", "")).strip())
        if provenance is None:
            unmatched.append(
                {
                    "fichier": str(path),
                    "source": source_site,
                    "raison": "Aucune correspondance trouvée dans l'index de collecte.",
                }
            )
            provenance = {"original_title": "", "source_url": "", "collection_date": ""}

        new_values = {
            "source_url": provenance["source_url"],
            "original_title": provenance["original_title"],
            "collection_date": provenance["collection_date"],
            "source_site": source_site,
        }
        status = {
            "fichier": str(path.relative_to(PROJECT_ROOT)),
            "source_site": source_site,
            "source_url_present": bool(new_values["source_url"]),
            "original_title_present": bool(new_values["original_title"]),
            "collection_date_present": bool(new_values["collection_date"]),
            "matching_method": matching_method,
        }
        rows.append(status)

        if apply and any(data.get(key) != value for key, value in new_values.items()):
            data.update(new_values)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed += 1

    by_source = Counter(row["source_site"] for row in rows)
    summary = []
    for source_site, count in sorted(by_source.items()):
        source_rows = [row for row in rows if row["source_site"] == source_site]
        summary.append(
            {
                "source_site": source_site,
                "records": count,
                "source_url_present": sum(row["source_url_present"] for row in source_rows),
                "original_title_present": sum(row["original_title_present"] for row in source_rows),
                "collection_date_present": sum(row["collection_date_present"] for row in source_rows),
            }
        )
    summary.append(
        {
            "source_site": "TOTAL",
            "records": len(rows),
            "source_url_present": sum(row["source_url_present"] for row in rows),
            "original_title_present": sum(row["original_title_present"] for row in rows),
            "collection_date_present": sum(row["collection_date_present"] for row in rows),
        }
    )
    ecrire_csv(
        REPORT_DIR / "provenance_coverage.csv",
        summary,
        ["source_site", "records", "source_url_present", "original_title_present", "collection_date_present"],
    )
    ecrire_csv(
        REPORT_DIR / "provenance_records.csv",
        rows,
        [
            "fichier",
            "source_site",
            "source_url_present",
            "original_title_present",
            "collection_date_present",
            "matching_method",
        ],
    )
    ecrire_csv(REPORT_DIR / "provenance_unmatched.csv", unmatched, ["fichier", "source", "raison"])

    print(f"Mode : {'apply' if apply else 'dry-run'}")
    print(f"Fiches JSON traitées : {len(rows)}")
    print(f"Fiches modifiées : {changed}")
    print(f"Correspondances introuvables : {len(unmatched)}")
    print(f"Rapports : {REPORT_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ajoute la provenance aux fiches JSON.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Crée les rapports sans modifier les JSON.")
    group.add_argument("--apply", action="store_true", help="Ajoute les champs de provenance dans les JSON.")
    args = parser.parse_args()
    traiter(apply=args.apply)


if __name__ == "__main__":
    main()
