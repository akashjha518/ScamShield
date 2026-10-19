
from backend.app.analyzer import analyze_message
from backend.app.rules import detect_findings


def test_explicit_registration_fee_is_detected_once():
    message = "You must pay a registration fee before starting work."

    findings = detect_findings(message)
    result = analyze_message(message)

    assert any(f.rule_id == "FEE_UPFRONT" for f in findings)
    assert not any(f.rule_id == "ADVANCE_PAYMENT" for f in findings)
    assert result.risk_score == 45
    assert result.risk_level == "CRITICAL"


def test_explicit_no_registration_fee_is_not_flagged():
    message = (
        "We are hiring a freelance data-entry assistant for 10 hours "
        "per week at an agreed hourly rate. No registration fee is "
        "required. Please review the contract and company details "
        "before accepting."
    )

    result = analyze_message(message)

    assert not any(
        finding.rule_id == "FEE_UPFRONT"
        for finding in result.findings
    )
    assert result.risk_score == 0


def test_ambiguous_offer_does_not_gain_points_for_missing_information():
    message = "We have a freelance opportunity available."

    result = analyze_message(message)

    assert result.risk_score == 0
    assert result.risk_level == "LOW"
    assert result.missing_information


def test_urgency_is_detected_with_supporting_evidence():
    message = "Act immediately. This is your last chance."

    findings = detect_findings(message)

    assert any(f.rule_id == "ARTIFICIAL_URGENCY" for f in findings)
    assert all(f.evidence in message for f in findings)


def test_sensitive_information_request_is_detected():
    message = "Please send your password to complete onboarding."

    findings = detect_findings(message)

    assert any(
        f.rule_id == "SENSITIVE_INFORMATION"
        for f in findings
    )


def test_blank_message_is_rejected_by_schema():
    from pydantic import ValidationError
    from backend.app.schemas import AnalysisRequest

    import pytest

    with pytest.raises(ValidationError):
        AnalysisRequest(message="   ")


def test_legitimate_looking_offer_has_no_fee_finding():
    message = (
        "We are hiring a freelance data-entry assistant for 10 hours "
        "per week at an agreed hourly rate. No registration fee is "
        "required. Please review the contract and company details "
        "before accepting."
    )

    result = analyze_message(message)

    assert result.risk_score == 0
    assert not result.findings


def test_payment_forwarding_request_is_detected():
    message = (
        "Receive the client's payment into your account and forward "
        "the money to our supplier."
    )

    findings = detect_findings(message)

    assert any(f.rule_id == "PAYMENT_REDIRECT" for f in findings)


def test_evidence_always_comes_from_submitted_message():
    message = (
        "Act immediately. Please send your password to complete onboarding."
    )

    findings = detect_findings(message)

    assert findings
    assert all(f.evidence in message for f in findings)


def test_no_findings_does_not_mean_declared_safe():
    result = analyze_message(
        "We have a freelance opportunity available."
    )

    assert result.risk_score == 0
    assert result.risk_level == "LOW"
    assert "does not establish" in result.summary


def test_multiple_distinct_indicators_increase_score():
    message = (
        "You must pay a registration fee before starting work. "
        "Please send your password to complete onboarding."
    )

    result = analyze_message(message)

    assert any(f.rule_id == "FEE_UPFRONT" for f in result.findings)
    assert any(
        f.rule_id == "SENSITIVE_INFORMATION"
        for f in result.findings
    )
    assert result.risk_score > 45
