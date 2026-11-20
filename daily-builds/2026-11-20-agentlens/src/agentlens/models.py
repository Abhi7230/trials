"""Data models for trace events and patterns."""

from typing import Any

from pydantic import BaseModel, Field


class TraceEvent(BaseModel):
    """Normalized trace event."""

    timestamp: str
    type: str  # "message" | "tool_call" | "tool_result"
    role: str | None = None  # "user" | "assistant" | "tool"
    content: str | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    error: str | None = None
    cost_usd: float | None = None
    latency_ms: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class PatternInstance(BaseModel):
    """A single instance of a detected pattern."""

    pattern_type: str
    severity: str
    deduction: int
    details: dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """Complete analysis result."""

    score: int
    passed: bool
    patterns: list[dict[str, Any]]
    stats: dict[str, Any]
