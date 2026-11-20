"""Score traces based on detected patterns."""

from typing import Any

from agentlens.detectors import get_all_detectors
from agentlens.models import AnalysisResult, PatternInstance, TraceEvent


def analyze_trace(
    events: list[TraceEvent], config: dict[str, Any] | None = None
) -> AnalysisResult:
    """
    Analyze a trace and compute reliability score.

    Returns an AnalysisResult with score (0-100), patterns, and stats.
    """
    config = config or {}

    # Run all detectors
    all_instances: list[PatternInstance] = []
    detectors = get_all_detectors()

    for detector_cls in detectors:
        detector = detector_cls()
        instances = detector.detect(events, config)
        all_instances.extend(instances)

    # Compute score
    score = 100

    # Sort by severity for consistent deduction order
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_instances = sorted(
        all_instances, key=lambda x: (severity_order.get(x.severity, 99), x.pattern_type)
    )

    for instance in sorted_instances:
        score -= instance.deduction

    score = max(0, score)  # Floor at 0

    # Group patterns by type
    patterns_by_type: dict[str, list[PatternInstance]] = {}
    for instance in all_instances:
        if instance.pattern_type not in patterns_by_type:
            patterns_by_type[instance.pattern_type] = []
        patterns_by_type[instance.pattern_type].append(instance)

    # Format patterns for output
    patterns = []
    for pattern_type, instances in patterns_by_type.items():
        first = instances[0]
        patterns.append(
            {
                "type": pattern_type,
                "severity": first.severity,
                "count": len(instances),
                "deduction": sum(inst.deduction for inst in instances),
                "instances": [inst.model_dump() for inst in instances],
            }
        )

    # Compute stats
    stats = _compute_stats(events)

    # Determine pass/fail
    fail_under = config.get("fail_under", 0)
    passed = score >= fail_under

    return AnalysisResult(score=score, passed=passed, patterns=patterns, stats=stats)


def _compute_stats(events: list[TraceEvent]) -> dict[str, Any]:
    """Compute trace statistics."""
    total_turns = sum(1 for e in events if e.type == "message")
    tool_calls = sum(1 for e in events if e.type == "tool_call")
    errors = sum(1 for e in events if e.type == "tool_result" and e.error)

    cost_usd = sum(e.cost_usd or 0.0 for e in events)

    # Compute duration (approximate from latencies)
    duration_ms = sum(e.latency_ms or 0.0 for e in events)

    return {
        "total_turns": total_turns,
        "tool_calls": tool_calls,
        "errors": errors,
        "cost_usd": round(cost_usd, 4),
        "duration_ms": round(duration_ms, 2),
    }
