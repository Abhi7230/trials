"""Retry storm detector."""

from typing import Any

from agentlens.detectors import register
from agentlens.models import PatternInstance, TraceEvent


@register
class RetryStormDetector:
    """Detect consecutive tool errors without success."""

    pattern_type = "retry-storm"
    severity = "high"
    deduction = 20

    def detect(
        self, events: list[TraceEvent], config: dict[str, Any] | None = None
    ) -> list[PatternInstance]:
        """Detect retry storms."""
        instances = []
        config = config or {}
        min_errors = config.get("retry_storm_min_errors", 5)

        consecutive_errors = 0

        for event in events:
            if event.type == "tool_result":
                if event.error:
                    consecutive_errors += 1
                else:
                    # Success, check if we had a storm
                    if consecutive_errors >= min_errors:
                        instances.append(
                            PatternInstance(
                                pattern_type=self.pattern_type,
                                severity=self.severity,
                                deduction=self.deduction,
                                details={"error_count": consecutive_errors},
                            )
                        )
                    consecutive_errors = 0

        # Check final state
        if consecutive_errors >= min_errors:
            instances.append(
                PatternInstance(
                    pattern_type=self.pattern_type,
                    severity=self.severity,
                    deduction=self.deduction,
                    details={"error_count": consecutive_errors},
                )
            )

        return instances
