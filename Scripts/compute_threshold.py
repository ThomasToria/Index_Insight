from __future__ import annotations

import numpy as np
from pathlib import Path
from typing import List

from score_keywords import analyze_file, find_txt_files, DATABASE_DIR


MIN_WORDS = 50
PERCENTILE = 5


def compute_scores() -> List[float]:
    txt_files = find_txt_files(DATABASE_DIR)

    scores = []

    for path in txt_files:
        result = analyze_file(path)

        if result["word_count"] >= MIN_WORDS:
            scores.append(result["score_normalized"])

    return scores


def compute_threshold(scores: List[float]) -> float:
    return float(np.percentile(scores, PERCENTILE))


def main():
    scores = compute_scores()

    if not scores:
        print("Aucun score valide.")
        return

    threshold = compute_threshold(scores)

    print("\n=== ANALYSE DES SCORES ===")
    print(f"Nombre de fichiers analysés : {len(scores)}")
    print(f"Score min                  : {min(scores):.8f}")
    print(f"Score médian               : {np.median(scores):.8f}")
    print(f"Score max                  : {max(scores):.8f}")
    print(f"\nSeuil recommandé ({PERCENTILE}e percentile) : {threshold:.8f}")

    below = [s for s in scores if s < threshold]
    print(f"Fichiers sous seuil        : {len(below)} ({len(below)/len(scores)*100:.2f}%)")


if __name__ == "__main__":
    main()