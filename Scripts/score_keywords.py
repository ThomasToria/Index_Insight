from __future__ import annotations

import csv
import re
import unicodedata
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "Scripts"

MIN_WORDS = 50
BOTTOM_N = 10
TOP_N = 10

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
    return len(normalized_text.split()) if normalized_text else 0


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


def analyze_file(file_path: Path, base_dir: Path) -> Dict[str, object]:
    raw_text = file_path.read_text(encoding="utf-8", errors="ignore")
    normalized = normalize_text(raw_text)
    filename_normalized = normalize_text(file_path.stem)

    word_count = count_words(normalized)

    keyword_counts = {}
    weighted_details = {}
    title_bonus_details = {}
    total_score = 0

    for keyword, weight in KEYWORDS.items():
        pattern = KEYWORD_PATTERNS[keyword]
        count = len(pattern.findall(normalized))
        title_bonus = 2 if pattern.search(filename_normalized) else 0

        keyword_counts[keyword] = count
        weighted_details[keyword] = count * weight
        title_bonus_details[keyword] = title_bonus
        total_score += count * weight + title_bonus

    score_normalized = total_score / word_count if word_count > 0 else 0.0

    return {
        "file_name": file_path.name,
        "relative_path": str(file_path.relative_to(base_dir)),
        "absolute_path": str(file_path.resolve()),
        "word_count": word_count,
        "score_raw": total_score,
        "score_normalized": score_normalized,
    }


def find_txt_files(target_dir: Path) -> List[Path]:
    return sorted(target_dir.rglob("*.txt"))


def main():
    if len(sys.argv) < 2:
        print("Usage: python score_keywords.py <dossier>")
        return

    target_dir = Path(sys.argv[1]).resolve()

    if not target_dir.exists():
        print(f"Dossier introuvable : {target_dir}")
        return

    print(f"\nDossier analysé : {target_dir}")

    txt_files = find_txt_files(target_dir)

    if not txt_files:
        print("Aucun fichier .txt trouvé.")
        return

    results = [analyze_file(path, target_dir) for path in txt_files]

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

    print(f"Nombre de fichiers : {len(results)}")

    print(f"\nTop {BOTTOM_N} plus faibles :\n")
    for i, r in enumerate(bottom, 1):
        print(f"{i}. {r['absolute_path']}:1 | score={r['score_normalized']:.6f}")

    print(f"\nTop {TOP_N} plus forts :\n")
    for i, r in enumerate(top, 1):
        print(f"{i}. {r['absolute_path']}:1 | score={r['score_normalized']:.6f}")


if __name__ == "__main__":
    main()