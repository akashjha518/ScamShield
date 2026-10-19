
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

Severity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class AnalysisRequest(BaseModel):
    """Validated message submitted for freelance scam analysis."""

    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="Freelance offer, client message, or payment request.",
    )

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message must not be blank.")
        return value


class Finding(BaseModel):
    """A detection finding supported by an observed message excerpt."""

    rule_id: str
    title: str
    severity: Severity
    points: int = Field(ge=0, le=100)
    evidence: str = Field(min_length=1)
    explanation: str
    category: str


class Recommendation(BaseModel):
    """A practical action relevant to the analysis."""

    priority: Literal["HIGH", "MEDIUM", "LOW"]
    action: str


class AnalysisResponse(BaseModel):
    """Structured result produced by the deterministic analyzer."""

    risk_level: RiskLevel
    risk_score: int = Field(ge=0, le=100)
    findings: list[Finding] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    summary: str
    limitations: list[str] = Field(default_factory=list)

    ai_explanations: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Optional AI explanations keyed by existing verified rule IDs. "
            "These do not determine findings, severity, or risk scores."
        ),
    )