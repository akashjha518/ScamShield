
from backend.app.rules import RuleMatch, detect_findings
from backend.app.schemas import (
    AnalysisResponse,
    Finding,
    Recommendation,
)


LIMITATIONS = [
    "This is a rule-based screening tool, not a definitive scam verdict.",
    "A message with no detected warning signs may still be fraudulent.",
    "Detection depends on the wording of the submitted message.",
]


def calculate_risk_score(findings: list[RuleMatch]) -> int:
    """Calculate a capped score from distinct detection rules."""

    # Each rule produces at most one finding. Use rule IDs as an
    # additional safeguard against accidental duplicate scoring.
    unique_points: dict[str, int] = {}

    for finding in findings:
        unique_points.setdefault(finding.rule_id, finding.points)

    return min(sum(unique_points.values()), 100)


def classify_risk(score: int) -> str:
    """Map the deterministic score to a risk category."""

    if score >= 45:
        return "CRITICAL"
    if score >= 25:
        return "HIGH"
    if score >= 10:
        return "MEDIUM"
    return "LOW"


def identify_missing_information(message: str) -> list[str]:
    """Report useful verification details not established by the text.

    Missing information is informational only and never adds risk points.
    """

    missing: list[str] = []
    lowered = message.lower()

    if not any(term in lowered for term in ("contract", "agreement")):
        missing.append("No contract or written agreement is mentioned.")

    if not any(
        term in lowered
        for term in ("company website", "company registration", "company details")
    ):
        missing.append("Company identity or independently verifiable details are not established.")

    if not any(
        term in lowered
        for term in ("payment terms", "hourly rate", "fixed price", "project rate")
    ):
        missing.append("Specific payment terms are not established.")

    return missing


def build_recommendations(
    findings: list[RuleMatch],
) -> list[Recommendation]:
    """Generate practical next steps based on detected indicators."""

    recommendations: list[Recommendation] = []
    categories = {finding.category for finding in findings}
    rule_ids = {finding.rule_id for finding in findings}

    if "FEE_UPFRONT" in rule_ids or "ADVANCE_PAYMENT" in rule_ids:
        recommendations.append(
            Recommendation(
                priority="HIGH",
                action=(
                    "Do not pay the requested fee or deposit until you have "
                    "independently verified the client and the reason for payment."
                ),
            )
        )

    if "PAYMENT_REDIRECT" in rule_ids:
        recommendations.append(
            Recommendation(
                priority="HIGH",
                action=(
                    "Do not receive, forward, refund, or transfer money on "
                    "another person's behalf. Verify any payment independently."
                ),
            )
        )

    if "SENSITIVE_INFORMATION" in rule_ids:
        recommendations.append(
            Recommendation(
                priority="HIGH",
                action=(
                    "Do not share passwords, OTPs, CVVs, or banking credentials. "
                    "Use official channels to verify any identity request."
                ),
            )
        )

    if "urgency" in categories:
        recommendations.append(
            Recommendation(
                priority="MEDIUM",
                action=(
                    "Take time to verify the offer. Do not let deadlines or "
                    "pressure prevent you from checking the details."
                ),
            )
        )

    recommendations.append(
        Recommendation(
            priority="MEDIUM",
            action=(
                "Verify the client through independently obtained contact "
                "details and review the contract and payment terms before "
                "accepting the work."
            ),
        )
    )

    return recommendations


def analyze_message(message: str) -> AnalysisResponse:
    """Analyze a freelance message using deterministic detection rules."""

    findings = detect_findings(message)
    score = calculate_risk_score(findings)
    risk_level = classify_risk(score)

    structured_findings = [
        Finding(
            rule_id=item.rule_id,
            title=item.title,
            severity=item.severity,
            points=item.points,
            evidence=item.evidence,
            explanation=item.explanation,
            category=item.category,
        )
        for item in findings
    ]

    if findings:
        summary = (
            f"Detected {len(findings)} warning sign(s). "
            f"The rule-based risk score is {score}/100 ({risk_level}). "
            "Review the evidence before deciding how to proceed."
        )
    else:
        summary = (
            "No warning signs covered by the current rules were detected. "
            "This does not establish that the offer is legitimate or safe."
        )

    return AnalysisResponse(
        risk_level=risk_level,
        risk_score=score,
        findings=structured_findings,
        missing_information=identify_missing_information(message),
        recommendations=build_recommendations(findings),
        summary=summary,
        limitations=LIMITATIONS,
    )
