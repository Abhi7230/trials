"""FastAPI service for agentlens."""

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agentlens.detectors import get_all_detectors
from agentlens.models import AnalysisResult, TraceEvent
from agentlens.scorer import analyze_trace

app = FastAPI(title="agentlens", version="0.1.0")

# Metrics (using globals for simple in-memory metrics)
_analysis_count = 0  # noqa: PLW0603
_total_score = 0  # noqa: PLW0603


class AnalyzeRequest(BaseModel):
    """Request body for /analyze."""

    trace: list[dict[str, Any]]
    options: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str


class MetricsResponse(BaseModel):
    """Metrics response."""

    analyses_count: int
    avg_score: float


class RuleInfo(BaseModel):
    """Rule information."""

    pattern_type: str
    severity: str
    deduction: int


@app.post("/analyze", response_model=AnalysisResult)
async def analyze(request: AnalyzeRequest) -> AnalysisResult:
    """Analyze a trace."""
    global _analysis_count, _total_score  # noqa: PLW0603

    try:
        # Parse trace events
        events = [TraceEvent(**event) for event in request.trace]

        # Build config from options
        config = request.options or {}

        # Analyze
        result = analyze_trace(events, config)

        # Update metrics
        _analysis_count += 1
        _total_score += result.score

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/rules", response_model=list[RuleInfo])
async def rules() -> list[RuleInfo]:
    """List all detection rules."""
    detectors = get_all_detectors()
    return [
        RuleInfo(
            pattern_type=detector_cls().pattern_type,
            severity=detector_cls().severity,
            deduction=detector_cls().deduction,
        )
        for detector_cls in detectors
    ]


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check."""
    return HealthResponse(status="ok")


@app.get("/metrics", response_model=MetricsResponse)
async def metrics() -> MetricsResponse:
    """Get service metrics."""
    avg = _total_score / _analysis_count if _analysis_count > 0 else 0.0
    return MetricsResponse(analyses_count=_analysis_count, avg_score=round(avg, 2))
