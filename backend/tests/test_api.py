
from fastapi.testclient import TestClient

from backend.app.main import app

from backend.app import main
from backend.app.ollama_client import OllamaError

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ScamShield API",
    }


def test_analyze_endpoint_detects_registration_fee():
    response = client.post(
        "/analyze",
        json={
            "message": (
                "You must pay a registration fee before starting work."
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["risk_level"] == "CRITICAL"
    assert data["risk_score"] == 45
    assert any(
        finding["rule_id"] == "FEE_UPFRONT"
        for finding in data["findings"]
    )


def test_analyze_endpoint_accepts_legitimate_looking_offer():
    response = client.post(
        "/analyze",
        json={
            "message": (
                "We are hiring a freelance data-entry assistant. "
                "No registration fee is required. Please review "
                "the contract and company details before accepting."
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["risk_score"] == 0
    assert data["findings"] == []


def test_analyze_endpoint_rejects_blank_message():
    response = client.post(
        "/analyze",
        json={"message": "   "},
    )

    assert response.status_code == 422


def test_analyze_endpoint_rejects_missing_message():
    response = client.post("/analyze", json={})

    assert response.status_code == 422


def test_analyze_endpoint_rejects_oversized_message():
    response = client.post(
        "/analyze",
        json={"message": "a" * 10_001},
    )

    assert response.status_code == 422


def test_analyze_endpoint_includes_ai_explanation(monkeypatch):
    def fake_explain(findings):
        assert findings
        return {
            findings[0]["rule_id"]: "Verify this payment request independently."
        }

    monkeypatch.setattr(main, "explain_findings", fake_explain)

    response = client.post(
        "/analyze",
        json={"message": "You must pay a registration fee before starting work."},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["risk_level"] == "CRITICAL"
    assert data["risk_score"] == 45
    assert data["findings"][0]["rule_id"] == "FEE_UPFRONT"
    assert data["ai_explanations"]["FEE_UPFRONT"] == (
        "Verify this payment request independently."
    )


def test_analyze_endpoint_falls_back_when_ollama_fails(monkeypatch):
    def fake_explain(findings):
        raise OllamaError("Ollama unavailable")

    monkeypatch.setattr(main, "explain_findings", fake_explain)

    response = client.post(
        "/analyze",
        json={"message": "You must pay a registration fee before starting work."},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["risk_level"] == "CRITICAL"
    assert data["risk_score"] == 45
    assert data["findings"][0]["rule_id"] == "FEE_UPFRONT"
    assert data["ai_explanations"] == {}


def test_analyze_endpoint_skips_ollama_without_findings(monkeypatch):
    def unexpected_call(findings):
        raise AssertionError("Ollama should not be called without findings")

    monkeypatch.setattr(main, "explain_findings", unexpected_call)

    response = client.post(
        "/analyze",
        json={
            "message": (
                "We have a freelance opportunity available."
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["risk_level"] == "LOW"
    assert data["risk_score"] == 0
    assert data["findings"] == []
    assert data["ai_explanations"] == {}
