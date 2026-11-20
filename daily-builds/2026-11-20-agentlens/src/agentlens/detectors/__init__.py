"""Detector registry and base protocol."""

from typing import Any, Protocol

from agentlens.models import PatternInstance, TraceEvent


class Detector(Protocol):
    """Protocol for pattern detectors."""

    pattern_type: str
    severity: str
    deduction: int

    def detect(
        self, events: list[TraceEvent], config: dict[str, Any] | None = None
    ) -> list[PatternInstance]:
        """Detect pattern instances in the trace."""
        ...


# Registry of all detectors
_DETECTORS: list[type[Detector]] = []


def register(detector_cls: type[Detector]) -> type[Detector]:
    """Register a detector."""
    _DETECTORS.append(detector_cls)
    return detector_cls


def get_all_detectors() -> list[type[Detector]]:
    """Get all registered detectors."""
    return _DETECTORS.copy()


# Import all detectors to trigger registration  # noqa: E402
from agentlens.detectors import (  # noqa: E402
    cost_blowup,
    error_ignored,
    hallucinated_tool,
    latency_outlier,
    loop,
    repeated,
    retry_storm,
    token_blowup,
)

__all__ = [
    "Detector",
    "register",
    "get_all_detectors",
    "loop",
    "repeated",
    "retry_storm",
    "error_ignored",
    "hallucinated_tool",
    "token_blowup",
    "cost_blowup",
    "latency_outlier",
]
