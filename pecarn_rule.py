#!/usr/bin/env python3
"""PECARN age-specific pediatric minor blunt head trauma rule (Kuppermann et al., 2009).

The result is a decision-rule category, NOT a numerical score or individualized risk estimate.
Designed for educational/clinician-support use; not a substitute for clinical judgment.
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Any

SOURCE = "Kuppermann et al. Lancet 2009;374:1160-1170. doi:10.1016/S0140-6736(09)61558-0"
YOUNG = ("palpable_skull_fracture", "nonfrontal_scalp_hematoma", "loc_at_least_5_seconds", "not_acting_normally")
OLDER = ("basilar_skull_fracture_signs", "any_loss_of_consciousness", "vomiting", "severe_headache")
SHARED = ("altered_mental_status", "severe_mechanism")
BOOLEAN_FIELDS = (*SHARED, *YOUNG, *OLDER)
COLUMNS = ("age_months", "gcs", "hours_since_injury", "exclusion_present", *BOOLEAN_FIELDS)
GUIDANCE = {
    "high": "CT recommended by the PECARN algorithm; arrange urgent clinical assessment.",
    "intermediate": "Observation versus CT; use clinical judgment, evolution of findings, and shared decision-making.",
    "very_low": "CT generally not recommended by PECARN for an otherwise eligible child; provide clinical reassessment and precautions.",
}


def _number(value: Any, name: str, *, integral: bool = False) -> float | int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not (float('-inf') < number < float('inf')):
        raise ValueError(f"{name} must be finite")
    if integral and not number.is_integer():
        raise ValueError(f"{name} must be an integer")
    return int(number) if integral else number


def _boolean(value: Any, name: str) -> bool:
    if type(value) is bool:
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "yes", "1"):
            return True
        if lowered in ("false", "no", "0"):
            return False
    raise ValueError(f"{name} must be explicitly true/false (or yes/no)")


def calculate_metrics(**kwargs: Any) -> dict[str, Any]:
    """Classify a fully assessed, eligible minor blunt head trauma case.

    All applicable findings must be provided explicitly (no missing = negative).
    The caller must confirm no study exclusion through ``exclusion_present=False``.
    The age-specific non-applicable findings must be omitted or left blank.
    """
    unknown = set(kwargs) - set(COLUMNS)
    if unknown:
        raise ValueError(f"Unknown input field(s): {', '.join(sorted(unknown))}")
    age = _number(kwargs.get("age_months"), "age_months", integral=True)
    gcs = _number(kwargs.get("gcs"), "gcs", integral=True)
    hours = _number(kwargs.get("hours_since_injury"), "hours_since_injury")
    if not 0 <= age < 216:
        raise ValueError("age_months must be between 0 and 215 (<18 years)")
    if gcs not in (14, 15):
        raise ValueError("PECARN minor head trauma rule applies to GCS 14-15 only")
    if not 0 <= hours <= 24:
        raise ValueError("PECARN study enrolled patients presenting within 24 hours")
    if _boolean(kwargs.get("exclusion_present"), "exclusion_present"):
        raise ValueError("Rule not applicable when a study exclusion or special population is present")

    applicable = SHARED + (YOUNG if age < 24 else OLDER)
    irrelevant = OLDER if age < 24 else YOUNG
    for key in irrelevant:
        if kwargs.get(key) not in (None, ""):
            raise ValueError(f"{key} does not apply to this age group; omit it")
    findings = {key: _boolean(kwargs.get(key), key) for key in applicable}

    high = ["GCS 14"] if gcs == 14 else []
    if findings["altered_mental_status"]:
        high.append("Altered mental status")
    if age < 24:
        if findings["palpable_skull_fracture"]:
            high.append("Palpable skull fracture")
        intermediate_labels = {
            "nonfrontal_scalp_hematoma": "Non-frontal scalp hematoma",
            "loc_at_least_5_seconds": "Loss of consciousness ≥5 seconds",
            "severe_mechanism": "Severe injury mechanism",
            "not_acting_normally": "Not acting normally according to parent",
        }
    else:
        if findings["basilar_skull_fracture_signs"]:
            high.append("Signs of basilar skull fracture")
        intermediate_labels = {
            "any_loss_of_consciousness": "Any loss of consciousness",
            "vomiting": "Vomiting",
            "severe_mechanism": "Severe injury mechanism",
            "severe_headache": "Severe headache",
        }

    intermediate = [label for key, label in intermediate_labels.items() if findings[key]]
    tier = "high" if high else "intermediate" if intermediate else "very_low"
    return {
        "tool": "pecarn-pediatric-head-injury",
        "age_group": "under_2" if age < 24 else "2_and_older",
        "risk_tier": tier,
        "predictors_present": high + intermediate,
        "ct_guidance": GUIDANCE[tier],
        "source": SOURCE,
        "note": "Rule categories are not a diagnosis or an individualized probability; eligibility and findings require clinician assessment.",
    }


def _csv_row(row: dict[str, str]) -> dict[str, Any]:
    # Blank age-inapplicable fields are intentionally omitted.
    return {k: v for k, v in row.items() if v is not None and str(v).strip() != ""}


def process_batch(input_csv: str, output_csv: str) -> int:
    """Validate every row before writing any output; reject unexpected columns/PHI."""
    src, dest = Path(input_csv), Path(output_csv)
    if src.resolve() == dest.resolve():
        raise ValueError("Input and output CSV paths must differ")
    with src.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fieldnames = reader.fieldnames or []
        if not fieldnames or len(set(fieldnames)) != len(fieldnames):
            raise ValueError("Input CSV needs a unique, non-empty header")
        unexpected = set(fieldnames) - set(COLUMNS)
        if unexpected:
            raise ValueError(f"Unexpected CSV columns (no identifiers/PHI permitted): {', '.join(sorted(unexpected))}")
        results = []
        for index, row in enumerate(reader, start=2):
            try:
                if None in row:
                    raise ValueError("Excess CSV values")
                result = calculate_metrics(**_csv_row(row))
            except ValueError as exc:
                raise ValueError(f"CSV row {index}: {exc}") from exc
            results.append({**row, "risk_tier": result["risk_tier"], "ct_guidance": result["ct_guidance"],
                            "predictors_present": "; ".join(result["predictors_present"])})
    with dest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=[*fieldnames, "risk_tier", "ct_guidance", "predictors_present"])
        writer.writeheader()
        writer.writerows(results)
    return len(results)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PECARN minor blunt head trauma educational decision rule")
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("single", help="Evaluate one eligible case")
    single.add_argument("--age-months", required=True, type=int)
    single.add_argument("--gcs", required=True, type=int)
    single.add_argument("--hours-since-injury", required=True, type=float)
    for name in ("exclusion_present", *BOOLEAN_FIELDS):
        single.add_argument("--" + name.replace("_", "-"), choices=["yes", "no"])
    batch = commands.add_parser("batch", help="Evaluate a CSV without identifiers")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            data = vars(args).copy()
            data.pop("command")
            print(json.dumps(calculate_metrics(**{k: v for k, v in data.items() if v is not None}), indent=2))
        else:
            print(f"Processed {process_batch(args.input, args.output)} cases -> {args.output}")
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
