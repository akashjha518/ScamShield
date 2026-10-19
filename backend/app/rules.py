
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RuleMatch:
    """Evidence-backed result from a single detection rule."""

    rule_id: str
    title: str
    severity: str
    points: int
    evidence: str
    explanation: str
    category: str


@dataclass(frozen=True)
class DetectionRule:
    """A deterministic rule used to identify a warning sign."""

    rule_id: str
    title: str
    severity: str
    points: int
    category: str
    explanation: str
    patterns: tuple[str, ...]


RULES: tuple[DetectionRule, ...] = (
    DetectionRule(
        rule_id="FEE_UPFRONT",
        title="Upfront registration or onboarding fee",
        severity="CRITICAL",
        points=45,
        category="payment",
        explanation=(
            "The message appears to require payment before work begins. "
            "Legitimate freelance work should be independently verified "
            "before paying a client or recruiter."
        ),
        patterns=(
            r"\b(?:pay|send|transfer|deposit|submit)\b"
            r".{0,100}\b(?:registration|register|onboarding|"
            r"activation|processing)\s+fee\b",
            r"\b(?:registration|onboarding|activation|processing)\s+fee\b"
            r".{0,100}\b(?:required|mandatory|must\s+pay|pay\s+first)\b",
            r"\bpay\s+(?:a|the|an)?\s*(?:registration|onboarding|"
            r"activation|processing)\s+fee\b",
        ),
    ),
    DetectionRule(
        rule_id="ADVANCE_PAYMENT",
        title="Advance payment demanded from the freelancer",
        severity="HIGH",
        points=30,
        category="payment",
        explanation=(
            "A demand for money before receiving work or payment can "
            "indicate an advance-fee scam. Verify the reason independently."
        ),
        patterns=(
            r"\b(?:pay|send|transfer|deposit)\b"
            r".{0,80}\b(?:upfront|in\s+advance|before\s+starting)\b",
            r"\b(?:security deposit|refundable deposit|"
            r"equipment deposit|training fee)\b",
        ),
    ),
    DetectionRule(
        rule_id="PAYMENT_REDIRECT",
        title="Unusual payment or money-transfer arrangement",
        severity="HIGH",
        points=30,
        category="payment",
        explanation=(
            "Requests to receive and forward money, pay a third party, "
            "or return an overpayment can expose freelancers to fraud."
        ),
        patterns=(
            r"\b(?:receive|accept|process)\b.{0,80}\bpayment\b"
            r".{0,80}\b(?:forward|transfer|send\s+back|return)\b",
            r"\b(?:overpayment|overpaid)\b.{0,80}\b"
            r"(?:refund|return|send\s+back|transfer)\b",
            r"\b(?:buy|purchase)\b.{0,60}\b(?:gift cards|"
            r"gift card|cryptocurrency)\b",
        ),
    ),
    DetectionRule(
        rule_id="SENSITIVE_INFORMATION",
        title="Request for sensitive personal or financial information",
        severity="HIGH",
        points=30,
        category="personal_information",
        explanation=(
            "Sharing passwords, one-time passcodes, or banking credentials "
            "with an unverified contact can enable account theft or fraud."
        ),
        patterns=(
            r"\b(?:share|send|provide|tell\s+me|give\s+me)\b"
            r".{0,60}\b(?:password|passcode|otp|one[- ]time\s+code|"
            r"banking credentials|cvv|security code)\b",
            r"\b(?:password|otp|one[- ]time\s+code|cvv)\b"
            r".{0,60}\b(?:required|needed|send|share|provide)\b",
        ),
    ),
    DetectionRule(
        rule_id="ARTIFICIAL_URGENCY",
        title="Pressure to act immediately",
        severity="MEDIUM",
        points=10,
        category="urgency",
        explanation=(
            "Pressure to act without time for verification can increase "
            "the chance of a rushed and unsafe decision. Urgency alone "
            "does not prove fraud."
        ),
        patterns=(
            r"\b(?:act|apply|pay|respond|accept)\b"
            r".{0,50}\b(?:immediately|right now|within minutes)\b",
            r"\b(?:offer expires|last chance|limited time only|"
            r"urgent action required)\b",
            r"\bno time for (?:questions|verification|a contract)\b",
        ),
    ),
)


def _extract_evidence(message: str, pattern: str) -> str | None:
    """Return the original-text excerpt matching a rule pattern."""

    match = re.search(pattern, message, flags=re.IGNORECASE | re.DOTALL)

    if not match:
        return None

    # Keep the evidence readable in the results dashboard.
    excerpt = match.group(0).strip()
    if len(excerpt) > 240:
        excerpt = excerpt[:237].rstrip() + "..."

    return excerpt



def detect_findings(message: str) -> list[RuleMatch]:
    """Run detection rules while avoiding negation and duplicate fee findings."""

    findings: list[RuleMatch] = []

    # Explicitly recognize common statements denying a registration fee.
    fee_denial_patterns = (
        r"\bno\s+(?:registration|onboarding|activation|processing)\s+fee\b",
        r"\bno\s+fee\s+(?:is\s+)?(?:required|charged|needed)\b",
        r"\b(?:do|does|will)\s+not\s+charge\b.{0,60}\bfee\b",
        r"\bwithout\s+(?:any\s+)?(?:registration|onboarding|activation)"
        r"\s+fee\b",
    )

    fee_is_denied = any(
        re.search(pattern, message, flags=re.IGNORECASE | re.DOTALL)
        for pattern in fee_denial_patterns
    )

    for rule in RULES:
        # Do not treat an explicit denial of a registration fee as a demand.
        if rule.rule_id == "FEE_UPFRONT" and fee_is_denied:
            continue

        for pattern in rule.patterns:
            evidence = _extract_evidence(message, pattern)

            if evidence is None:
                continue

            # A registration-fee demand already represents an upfront
            # payment demand. Avoid counting the same fee twice.
            if (
                rule.rule_id == "ADVANCE_PAYMENT"
                and any(f.rule_id == "FEE_UPFRONT" for f in findings)
                and re.search(
                    r"\b(?:registration|onboarding|activation|processing)\s+fee\b",
                    evidence,
                    flags=re.IGNORECASE,
                )
            ):
                continue

            findings.append(
                RuleMatch(
                    rule_id=rule.rule_id,
                    title=rule.title,
                    severity=rule.severity,
                    points=rule.points,
                    evidence=evidence,
                    explanation=rule.explanation,
                    category=rule.category,
                )
            )
            break

    return findings

