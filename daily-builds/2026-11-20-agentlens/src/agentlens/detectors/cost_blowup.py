"""Cost blowup detector."""

from typing import Any

from agentlens.detectors import register
from agentlens.models import PatternInstance, TraceEvent


@register
class CostBlowupDetector:
    """Detect excessive costs."""

    pattern_type = "cost-blowup"
    severity = "medium"
    deduction = 10

    def detect(
        self, events: list[TraceEvent], config: dict[str, Any] | None = None
    ) -> list[PatternInstance]:
        """Detect cost blowup."""
        instances = []
        config = config or {}
        cost_limit = config.get("cost_limit_usd", 5.00)

        cumulative_cost = 0.0

        for event in events:
            if event.cost_usd:
                cumulative_cost += event.cost_usd

        if cumulative_cost > cost_limit:
            instances.append(
                PatternInstance(
                    pattern_type=self.pattern_type,
                    severity=self.severity,
                    deduction=self.deduction,
                    details={"cost_usd": cumulative_cost},
                )
            )

        return instances
