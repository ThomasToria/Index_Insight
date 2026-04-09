from __future__ import annotations

import csv
import re
import unicodedata
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_ROOT / "Database"
OUTPUT_DIR = PROJECT_ROOT / "Scripts"

MIN_WORDS = 50
BOTTOM_N = 10
TOP_N = 10

FULL_RESULTS_CSV = OUTPUT_DIR / "keyword_scores_full.csv"
BOTTOM_RESULTS_CSV = OUTPUT_DIR / "keyword_scores_bottom_10.csv"
TOP_RESULTS_CSV = OUTPUT_DIR / "keyword_scores_top_10.csv"


KEYWORDS = OrderedDict({
    "agisme": 5,
    "ville amie des aines": 5,
    "vada": 5,
    "vieillissement": 3,
    "personnes agees": 3,
    "aine": 3,
    "seniors": 3,
    "retraites": 3,
    "vieillir": 3,
    "retraite": 3,
    "age": 3,
    "intergenerationnel": 3,
    "chez soi": 1,
    "ehpad": 1,
    "mobilite": 1,
    "hebergement": 1,
    "autonomie": 1,
    "citoyen": 1,
    "fragile": 1,
    "vulnerable": 1,
    "dependant": 1,
    "isole": 1,
    "aidant": 1,
})


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def normalize_text(text: str) -> str:
    text = text.lower()
    text = strip_accents(text)
    text = text.replace("’", "'").replace("`", "'")
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("-", " ")
    text = text.replace("'", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def count_words(normalized_text: str) -> int:
    if not normalized_text:
        return 0
    return len(normalized_text.split())


def build_keyword_pattern(keyword: str) -> re.Pattern:
    tokens = keyword.split()

    if keyword == "isole":
        return re.compile(r"\bisol\w*\b", re.IGNORECASE)

    if len(tokens) == 1:
        return re.compile(rf"\b{re.escape(tokens[0])}\b", re.IGNORECASE)

    pattern = r"\b" + r"\s+".join(re.escape(t) for t in tokens) + r"\b"
    return re.compile(pattern, re.IGNORECASE)


KEYWORD_PATTERNS = {
    keyword: build_keyword_pattern(keyword)
    for keyword in KEYWORDS
}


def analyze_file(file_path: Path) -> Dict[str, object]:
    raw_text = file_path.read_text(encoding="utf-8", errors="ignore")
    normalized = normalize_text(raw_text)
    filename_normalized = normalize_text(file_path.stem)

    word_count = count_words(normalized)

    keyword_counts: Dict[str, int] = {}
    weighted_details: Dict[str, int] = {}
    title_bonus_details: Dict[str, int] = {}
    total_score = 0

    for keyword, weight in KEYWORDS.items():
        pattern = KEYWORD_PATTERNS[keyword]
        count = len(pattern.findall(normalized))
        title_bonus = 2 if pattern.search(filename_normalized) else 0

        keyword_counts[keyword] = count
        weighted_details[keyword] = count * weight
        title_bonus_details[keyword] = title_bonus
        total_score += count * weight + title_bonus

    score_normalized = (total_score / word_count) if word_count > 0 else 0.0

    return {
        "file_name": file_path.name,
        "relative_path": str(file_path.relative_to(PROJECT_ROOT)),
        "absolute_path": str(file_path.resolve()),
        "word_count": word_count,
        "score_raw": total_score,
        "score_normalized": score_normalized,
        "keyword_counts": keyword_counts,
        "weighted_details": weighted_details,
        "title_bonus_details": title_bonus_details,
    }


def find_txt_files(database_dir: Path) -> List[Path]:
    return sorted(database_dir.rglob("*.txt"))


def write_full_results_csv(results: List[Dict[str, object]], output_path: Path) -> None:
    fieldnames = [
        "file_name",
        "relative_path",
        "absolute_path",
        "word_count",
        "score_raw",
        "score_normalized",
    ]

    for keyword in KEYWORDS:
        fieldnames.append(f"count__{keyword}")

    for keyword in KEYWORDS:
        fieldnames.append(f"weighted__{keyword}")

    for keyword in KEYWORDS:
        fieldnames.append(f"title_bonus__{keyword}")

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for result in results:
            row = {
                "file_name": result["file_name"],
                "relative_path": result["relative_path"],
                "absolute_path": result["absolute_path"],
                "word_count": result["word_count"],
                "score_raw": result["score_raw"],
                "score_normalized": f"{result['score_normalized']:.8f}",
            }

            keyword_counts = result["keyword_counts"]
            weighted_details = result["weighted_details"]
            title_bonus_details = result["title_bonus_details"]

            for keyword in KEYWORDS:
                row[f"count__{keyword}"] = keyword_counts[keyword]

            for keyword in KEYWORDS:
                row[f"weighted__{keyword}"] = weighted_details[keyword]

            for keyword in KEYWORDS:
                row[f"title_bonus__{keyword}"] = title_bonus_details[keyword]

            writer.writerow(row)


def write_ranked_results_csv(
    results: List[Dict[str, object]],
    output_path: Path,
    n: int,
    reverse: bool,
) -> None:
    eligible = [r for r in results if r["word_count"] >= MIN_WORDS]

    if reverse:
        ranked = sorted(
            eligible,
            key=lambda r: (r["score_normalized"], r["score_raw"], r["word_count"]),
            reverse=True
        )[:n]
    else:
        ranked = sorted(
            eligible,
            key=lambda r: (r["score_normalized"], r["word_count"], r["score_raw"])
        )[:n]

    fieldnames = [
        "rank",
        "file_name",
        "relative_path",
        "absolute_path",
        "word_count",
        "score_raw",
        "score_normalized",
    ]

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for i, result in enumerate(ranked, start=1):
            writer.writerow({
                "rank": i,
                "file_name": result["file_name"],
                "relative_path": result["relative_path"],
                "absolute_path": result["absolute_path"],
                "word_count": result["word_count"],
                "score_raw": result["score_raw"],
                "score_normalized": f"{result['score_normalized']:.8f}",
            })


def print_summary(results: List[Dict[str, object]]) -> None:
    total_files = len(results)
    eligible = [r for r in results if r["word_count"] >= MIN_WORDS]

    bottom = sorted(
        eligible,
        key=lambda r: (r["score_normalized"], r["word_count"], r["score_raw"])
    )[:BOTTOM_N]

    top = sorted(
        eligible,
        key=lambda r: (r["score_normalized"], r["score_raw"], r["word_count"]),
        reverse=True
    )[:TOP_N]

    print(f"\nProjet racine      : {PROJECT_ROOT}")
    print(f"Dossier analysé    : {DATABASE_DIR}")
    print(f"Nombre de fichiers : {total_files}")
    print(f"Seuil min. de mots : {MIN_WORDS}")
    print(f"CSV complet        : {FULL_RESULTS_CSV}")
    print(f"CSV bottom {BOTTOM_N:<2}     : {BOTTOM_RESULTS_CSV}")
    print(f"CSV top {TOP_N:<5}      : {TOP_RESULTS_CSV}")

    print(f"\nTop {BOTTOM_N} des textes au score normalisé le plus bas :\n")
    for i, result in enumerate(bottom, start=1):
        clickable_path = f"{result['absolute_path']}:1"
        print(
            f"{i:>2}. "
            f"{clickable_path} | "
            f"mots={result['word_count']} | "
            f"score_brut={result['score_raw']} | "
            f"score_norm={result['score_normalized']:.8f}"
        )

    print(f"\nTop {TOP_N} des textes au score normalisé le plus élevé :\n")
    for i, result in enumerate(top, start=1):
        clickable_path = f"{result['absolute_path']}:1"
        print(
            f"{i:>2}. "
            f"{clickable_path} | "
            f"mots={result['word_count']} | "
            f"score_brut={result['score_raw']} | "
            f"score_norm={result['score_normalized']:.8f}"
        )


def main() -> None:
    if not DATABASE_DIR.exists():
        raise FileNotFoundError(f"Dossier introuvable : {DATABASE_DIR}")

    txt_files = find_txt_files(DATABASE_DIR)

    if not txt_files:
        print("Aucun fichier .txt trouvé dans Database.")
        return

    results = [analyze_file(path) for path in txt_files]

    results_sorted = sorted(
        results,
        key=lambda r: (r["score_normalized"], -r["score_raw"], r["file_name"])
    )

    write_full_results_csv(results_sorted, FULL_RESULTS_CSV)
    write_ranked_results_csv(results_sorted, BOTTOM_RESULTS_CSV, BOTTOM_N, reverse=False)
    write_ranked_results_csv(results_sorted, TOP_RESULTS_CSV, TOP_N, reverse=True)
    print_summary(results_sorted)


if __name__ == "__main__":
    main()