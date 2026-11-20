"""Repeated identical calls detector."""

import json
from collections import Counter
from typing import Any

from agentlens.detectors import register
from agentlens.models import PatternInstance, TraceEvent


@register
class RepeatedIdenticalCallsDetector:
    """Detect when the same tool+args combination appears more than twice."""

    pattern_type = "repeated-identical-calls"
    severity = "low"
    deduction = 5

    def detect(
        self, events: list[TraceEvent], config: dict[str, Any] | None = None
    ) -> list[PatternInstance]:
        """Detect repeated identical calls."""
        instances = []
        config = config or {}
        max_allowed = config.get("repeated_max_allowed", 2)

        # Count (tool, args) combinations
        call_counts: Counter[str] = Counter()

        for event in events:
            if event.type == "tool_call":
                key = f"{event.tool_name}::{json.dumps(event.tool_args or {}, sort_keys=True)}"
                call_counts[key] += 1

        # Find violations
        for key, count in call_counts.items():
            if count > max_allowed:
                tool_name = key.split("::", 1)[0]
                instances.append(
                    PatternInstance(
                        pattern_type=self.pattern_type,
                        severity=self.severity,
                        deduction=self.deduction,
                        details={"tool": tool_name, "count": count},
                    )
                )

        return instances
