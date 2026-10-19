
import json

import httpx
import pytest

from backend.app import ollama_client
from backend.app.ollama_client import OllamaError, explain_findings


FINDINGS = [
    {
        "rule_id": "FEE_UPFRONT",
        "title": "Upfront registration fee",
        "evidence": "pay a registration fee",
        "severity": "CRITICAL",
        "points": 45,
    }
]


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self.data


class FakeClient:
    def __init__(self, response=None, error=None, **kwargs):
        self.response = response
        self.error = error
        self.payload = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, json):
        self.payload = json

        if self.error:
            raise self.error

        return self.response


def install_fake_client(monkeypatch, response=None, error=None):
    fake = FakeClient(response=response, error=error)

    monkeypatch.setattr(
        ollama_client.httpx,
        "Client",
        lambda **kwargs: fake,
    )

    return fake


def model_response(explanations):
    return FakeResponse({
        "response": json.dumps({
            "explanations": explanations,
        })
    })


def test_valid_explanation_is_returned(monkeypatch):
    install_fake_client(
        monkeypatch,
        response=model_response([
            {
                "rule_id": "FEE_UPFRONT",
                "explanation": (
                    "The message requests payment before work begins. "
                    "Verify the request independently."
                ),
            }
        ]),
    )

    result = explain_findings(FINDINGS)

    assert list(result) == ["FEE_UPFRONT"]
    assert "payment before work begins" in result["FEE_UPFRONT"]


def test_empty_findings_do_not_call_ollama(monkeypatch):
    def unexpected_call(**kwargs):
        pytest.fail("Ollama should not be called without findings")

    monkeypatch.setattr(
        ollama_client.httpx,
        "Client",
        unexpected_call,
    )

    assert explain_findings([]) == {}


def test_unknown_rule_id_is_rejected(monkeypatch):
    install_fake_client(
        monkeypatch,
        response=model_response([
            {
                "rule_id": "INVENTED_SCAM",
                "explanation": "This is a scam.",
            }
        ]),
    )

    with pytest.raises(OllamaError, match="rule ID"):
        explain_findings(FINDINGS)


def test_missing_explanation_is_rejected(monkeypatch):
    install_fake_client(
        monkeypatch,
        response=model_response([]),
    )

    with pytest.raises(OllamaError, match="rule ID"):
        explain_findings(FINDINGS)


def test_malformed_json_is_rejected(monkeypatch):
    install_fake_client(
        monkeypatch,
        response=FakeResponse({
            "response": "This is not valid JSON"
        }),
    )

    with pytest.raises(OllamaError, match="malformed"):
        explain_findings(FINDINGS)


def test_ollama_timeout_is_handled(monkeypatch):
    install_fake_client(
        monkeypatch,
        error=httpx.TimeoutException("Request timed out"),
    )

    with pytest.raises(OllamaError, match="unavailable"):
        explain_findings(FINDINGS)


def test_http_error_is_handled(monkeypatch):
    request = httpx.Request(
        "POST",
        "http://localhost:11434/api/generate",
    )
    error = httpx.ConnectError(
        "Connection refused",
        request=request,
    )

    install_fake_client(monkeypatch, error=error)

    with pytest.raises(OllamaError, match="unavailable"):
        explain_findings(FINDINGS)


def test_model_cannot_return_extra_fields(monkeypatch):
    install_fake_client(
        monkeypatch,
        response=model_response([
            {
                "rule_id": "FEE_UPFRONT",
                "explanation": "Verify the payment request.",
                "risk_score": 0,
            }
        ]),
    )

    with pytest.raises(OllamaError, match="unexpected fields"):
        explain_findings(FINDINGS)


def test_original_findings_are_not_modified(monkeypatch):
    original = [finding.copy() for finding in FINDINGS]

    install_fake_client(
        monkeypatch,
        response=model_response([
            {
                "rule_id": "FEE_UPFRONT",
                "explanation": "Verify the request before paying.",
            }
        ]),
    )

    explain_findings(FINDINGS)

    assert FINDINGS == original
    assert FINDINGS[0]["points"] == 45
    assert FINDINGS[0]["severity"] == "CRITICAL"
