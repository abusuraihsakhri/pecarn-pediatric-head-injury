import csv
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pecarn_rule import calculate_metrics, process_batch


def young(**overrides):
    case = dict(age_months=10, gcs=15, hours_since_injury=2, exclusion_present=False,
                altered_mental_status=False, severe_mechanism=False,
                palpable_skull_fracture=False, nonfrontal_scalp_hematoma=False,
                loc_at_least_5_seconds=False, not_acting_normally=False)
    case.update(overrides)
    return case


def older(**overrides):
    case = dict(age_months=60, gcs=15, hours_since_injury=2, exclusion_present=False,
                altered_mental_status=False, severe_mechanism=False,
                basilar_skull_fracture_signs=False, any_loss_of_consciousness=False,
                vomiting=False, severe_headache=False)
    case.update(overrides)
    return case


@pytest.mark.parametrize("case,expected", [
    (young(), "very_low"), (older(), "very_low"),
    (young(gcs=14), "high"), (older(gcs=14), "high"),
    (young(altered_mental_status=True), "high"), (older(altered_mental_status=True), "high"),
    (young(palpable_skull_fracture=True), "high"),
    (older(basilar_skull_fracture_signs=True), "high"),
    (young(nonfrontal_scalp_hematoma=True), "intermediate"),
    (young(loc_at_least_5_seconds=True), "intermediate"),
    (young(not_acting_normally=True), "intermediate"),
    (young(severe_mechanism=True), "intermediate"),
    (older(any_loss_of_consciousness=True), "intermediate"),
    (older(vomiting=True), "intermediate"),
    (older(severe_headache=True), "intermediate"),
    (older(severe_mechanism=True), "intermediate"),
    (young(gcs=14, severe_mechanism=True), "high"),
    (older(basilar_skull_fracture_signs=True, vomiting=True), "high"),
    (young(age_months=23), "very_low"), (older(age_months=24), "very_low"),
])
def test_age_specific_branches(case, expected):
    assert calculate_metrics(**case)["risk_tier"] == expected


@pytest.mark.parametrize("changes", [
    {"gcs": 13}, {"gcs": 16}, {"gcs": 14.5}, {"age_months": -1},
    {"age_months": 216}, {"age_months": 2.5}, {"hours_since_injury": -1},
    {"hours_since_injury": 25}, {"hours_since_injury": float('nan')},
    {"exclusion_present": True}, {"altered_mental_status": None},
    {"altered_mental_status": "maybe"}, {"scalp_fracture": False},
    {"vomiting": False},
])
def test_invalid_cases_fail_closed(changes):
    with pytest.raises(ValueError):
        calculate_metrics(**young(**changes))


def test_older_requires_all_applicable_findings():
    item = older()
    item.pop("vomiting")
    with pytest.raises(ValueError, match="vomiting"):
        calculate_metrics(**item)


def test_under_two_loc_less_than_5_does_not_trigger():
    assert calculate_metrics(**young(loc_at_least_5_seconds=False))["risk_tier"] == "very_low"


def test_older_any_loc_triggers():
    assert calculate_metrics(**older(any_loss_of_consciousness=True))["risk_tier"] == "intermediate"


def test_batch_roundtrip_and_invalid_row(tmp_path):
    p_in, p_out = tmp_path / "in.csv", tmp_path / "out.csv"
    with p_in.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(older()))
        writer.writeheader()
        writer.writerow(older())
        writer.writerow(older(vomiting=True))
    assert process_batch(str(p_in), str(p_out)) == 2
    with p_out.open(newline="") as file:
        rows = list(csv.DictReader(file))
    assert [r["risk_tier"] for r in rows] == ["very_low", "intermediate"]
    with p_in.open("a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(older()))
        writer.writerow(older(vomiting="unknown"))
    with pytest.raises(ValueError, match="row 4"):
        process_batch(str(p_in), str(p_out))
    assert p_out.read_text()


def test_reject_unknown_identifier_columns(tmp_path):
    p = tmp_path / "in.csv"
    p.write_text("patient_name,age_months\nAlice,22\n")
    with pytest.raises(ValueError, match="Unexpected CSV columns"):
        process_batch(str(p), str(tmp_path / "out.csv"))


def test_reject_in_place_output(tmp_path):
    p = tmp_path / "input.csv"
    p.write_text("age_months\n12\n")
    with pytest.raises(ValueError, match="must differ"):
        process_batch(str(p), str(p))
