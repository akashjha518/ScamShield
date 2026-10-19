
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.analyzer import analyze_message
from backend.app.ollama_client import OllamaError, explain_findings
from backend.app.schemas import AnalysisRequest, AnalysisResponse


app = FastAPI(
    title="ScamShield API",
    description=(
        "Evidence-based freelance scam screening with deterministic "
        "rules and optional local AI explanations."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Confirm that the API is running."""

    return {"status": "ok", "service": "ScamShield API"}


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(request: AnalysisRequest) -> AnalysisResponse:
    """Run deterministic analysis and optionally explain its findings."""

    # The deterministic analyzer remains authoritative.
    result = analyze_message(request.message)

    # No findings means no need to call the language model.
    if not result.findings:
        return result

    try:
        explanations = explain_findings(
            [
                finding.model_dump()
                for finding in result.findings
            ]
        )

        # Attach explanations only. Do not modify scores, findings,
        # evidence, severity, risk level, or recommendations.
        result.ai_explanations = explanations

    except OllamaError:
        # AI is optional: retain the complete deterministic result.
        result.ai_explanations = {}

    return result


@app.exception_handler(Exception)
async def unexpected_error_handler(request, exc: Exception) -> JSONResponse:
    """Return a generic response for unexpected server errors."""

    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected internal server error occurred."},
    )
