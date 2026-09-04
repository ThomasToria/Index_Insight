r"""Repair a small set of safe metadata inconsistencies in the main database.

The script only applies deterministic repairs derived from existing fields:
an empty title is replaced by ``original_title`` (without a file extension), an
empty audience becomes ``public non connu``, and a list of initiative holders is
flattened to their explicitly provided names. Run without ``--apply`` first.

Examples:
    py .\Scripts\repair_metadata_from_provenance.py
    py .\Scripts\repair_metadata_from_provenance.py --apply
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE = PROJECT_ROOT / "LLM_Tagged_Database"
REPORT = PROJECT_ROOT / "outputs" / "quality_checks" / "metadata_repairs.csv"


def empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def clean_title(value: str) -> str:
    suffixes = (".pdf", ".docx", ".doc", ".txt")
    text = value.strip()
    return text[: -len(next(suffix for suffix in suffixes if text.lower().endswith(suffix)))] if text.lower().endswith(suffixes) else text


def planned_changes(record: dict[str, Any]) -> list[tuple[str, Any, Any]]:
    changes: list[tuple[str, Any, Any]] = []
    if empty(record.get("titre")) and isinstance(record.get("original_title"), str):
        title = clean_title(record["original_title"])
        if title:
            changes.append(("titre", record.get("titre", ""), title))
    if empty(record.get("public_vise")):
        changes.append(("public_vise", record.get("public_vise", ""), "public non connu"))
    holder = record.get("porteur_initiative")
    if isinstance(holder, list):
        names = [item.get("nom", "").strip() for item in holder if isinstance(item, dict) and item.get("nom")]
        if names:
            changes.append(("porteur_initiative", holder, " ; ".join(names)))
    return changes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write the deterministic repairs to the JSON files.")
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    for path in sorted(DATABASE.rglob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            record = json.load(handle)
        if not isinstance(record, dict):
            continue
        changes = planned_changes(record)
        for field, previous, replacement in changes:
            rows.append({
                "file": str(path.relative_to(PROJECT_ROOT)),
                "field": field,
                "previous_value": json.dumps(previous, ensure_ascii=False),
                "replacement_value": json.dumps(replacement, ensure_ascii=False),
                "applied": str(args.apply).lower(),
            })
            if args.apply:
                record[field] = replacement
        if args.apply and changes:
            with path.open("w", encoding="utf-8") as handle:
                json.dump(record, handle, ensure_ascii=False, indent=2)
                handle.write("\n")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "field", "previous_value", "replacement_value", "applied"])
        writer.writeheader()
        writer.writerows(rows)
    mode = "Applied" if args.apply else "Planned"
    print(f"{mode} {len(rows)} deterministic metadata repairs.")
    print(f"Report written to: {REPORT}")


if __name__ == "__main__":
    main()
