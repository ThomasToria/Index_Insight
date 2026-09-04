r"""Validate JSON files in the main LLM-tagged database without modifying them.

Examples:
    py .\Scripts\validate_llm_database.py
    py .\Scripts\validate_llm_database.py --output outputs\quality_checks\check.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "LLM_Tagged_Database"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "quality_checks" / "llm_database_validation.csv"

REQUIRED_FIELDS: dict[str, type | tuple[type, ...]] = {
    "titre": str,
    "territoire": (str, list),
    "echelle": list,
    "public_vise": str,
    "nature_initiative": str,
    "description": dict,
    "porteur_initiative": str,
    "date": list,
    "thematique": list,
    "source_site": str,
}
DESCRIPTION_FIELDS = {
    "description_generale",
    "contexte",
    "problematique",
    "solution_envisagee",
    "objectifs",
}


def is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip()) or (
        isinstance(value, (list, dict)) and not value
    )


def validate_record(path: Path) -> dict[str, str]:
    row = {
        "file": str(path.relative_to(PROJECT_ROOT)),
        "status": "valid",
        "missing_fields": "",
        "type_issues": "",
        "empty_core_fields": "",
        "missing_description_fields": "",
    }
    try:
        with path.open("r", encoding="utf-8") as handle:
            record = json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        row["status"] = "invalid_json"
        row["type_issues"] = str(error)
        return row

    if not isinstance(record, dict):
        row["status"] = "invalid_schema"
        row["type_issues"] = "top_level_not_object"
        return row

    missing = [field for field in REQUIRED_FIELDS if field not in record]
    type_issues = [
        field
        for field, expected_type in REQUIRED_FIELDS.items()
        if field in record and not isinstance(record[field], expected_type)
    ]
    empty_core = [
        field
        for field in ("titre", "public_vise", "nature_initiative", "source_site")
        if is_empty(record.get(field))
    ]
    description = record.get("description")
    missing_description = (
        [field for field in DESCRIPTION_FIELDS if field not in description]
        if isinstance(description, dict)
        else []
    )

    row["missing_fields"] = "|".join(sorted(missing))
    row["type_issues"] = "|".join(sorted(type_issues))
    row["empty_core_fields"] = "|".join(empty_core)
    row["missing_description_fields"] = "|".join(sorted(missing_description))
    if missing or type_issues:
        row["status"] = "invalid_schema"
    elif empty_core or missing_description:
        row["status"] = "review"
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    input_dir = args.input.resolve()
    output_file = args.output.resolve()
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Main database not found: {input_dir}")

    rows = [validate_record(path) for path in sorted(input_dir.rglob("*.json"))]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["file", "status"])
        writer.writeheader()
        writer.writerows(rows)

    counts = {status: sum(row["status"] == status for row in rows) for status in {row["status"] for row in rows}}
    print(f"Validated {len(rows)} JSON files.")
    print(", ".join(f"{status}: {count}" for status, count in sorted(counts.items())))
    print(f"Report written to: {output_file}")


if __name__ == "__main__":
    main()
