"""HTTP routes and tamper-evidence contract tests."""
from fastapi.testclient import TestClient
from agents.api import app
from agents.base import AuditTrail


def case():
    return {
        "age_months": 60, "gcs": 15, "hours_since_injury": 1,
        "exclusion_present": False, "altered_mental_status": False,
        "severe_mechanism": False, "basilar_skull_fracture_signs": False,
        "any_loss_of_consciousness": False, "vomiting": False,
        "severe_headache": False
    }


def test_pecarn_api_and_served_browser():
    with TestClient(app) as client:
        res = client.post("/api/pecarn", json=case())
        assert res.status_code == 200
        assert res.json()["risk_tier"] == "very_low"
        assert client.get("/").status_code == 200
        assert "PECARN Pediatric Head Injury" in client.get("/").text
        assert "function assess" in client.get("/app.js").text
        assert client.get("/health").status_code == 200


def test_api_intermediate_and_reject_inapplicable():
    with TestClient(app) as client:
        data = case()
        data["vomiting"] = True
        assert client.post("/api/pecarn", json=data).json()["risk_tier"] == "intermediate"
        data["age_months"] = 12
        assert client.post("/api/pecarn", json=data).status_code == 422
        data = case()
        del data["vomiting"]
        assert client.post("/api/pecarn", json=data).status_code == 422
        assert client.post("/api/pecarn", json={**case(), "gcs": 13}).status_code == 422
        assert client.post("/api/pecarn", json={**case(), "name": "patient"}).status_code == 422


def test_in_memory_audit_detects_tampering():
    audit = AuditTrail(secret_key="test-key-only")
    audit.log("test", "user", "VALIDATE", {"key": "value"})
    audit.log("test", "user", "COMPLETE", {"count": 2})
    assert audit.verify_integrity()
    exported = audit.get_trail()
    exported[0]["actor"] = "modified"
    assert audit.verify_integrity()  # returned copies cannot alter the actual log
    audit.logs[0]["actor"] = "modified"
    assert not audit.verify_integrity()
