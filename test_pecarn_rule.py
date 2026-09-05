import pytest
from pecarn_rule import calculate_metrics, process_batch


def test_pecarn_rule_single():
    res = calculate_metrics(v1=12.0, v2=4.0)
    assert "score" in res
    assert "classification" in res
    assert res["score"] > 0


def test_pecarn_rule_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "score" in content


def test_pecarn_rule_classification_tiers():
    """Test all three classification tiers."""
    low = calculate_metrics(v1=5.0)
    assert low["classification"] == "Low / Standard"

    moderate = calculate_metrics(v1=15.0)
    assert moderate["classification"] == "Moderate / Intermediate"

    high = calculate_metrics(v1=30.0)
    assert high["classification"] == "High / Severe"


def test_pecarn_rule_batch_file_not_found():
    """process_batch raises FileNotFoundError for missing input."""
    with pytest.raises(FileNotFoundError):
        process_batch("nonexistent.csv", "output.csv")


def test_pecarn_rule_empty_params():
    """calculate_metrics handles empty parameters gracefully."""
    res = calculate_metrics()
    assert res["score"] == 1.0
    assert res["inputs_evaluated"] == 0


def test_pecarn_rule_mixed_types():
    """calculate_metrics handles mixed numeric and string inputs."""
    res = calculate_metrics(v1=10.0, v2="non_numeric", v3=5.0)
    assert res["score"] > 0
    assert res["inputs_evaluated"] == 3
