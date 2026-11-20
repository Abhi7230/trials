"""Error ignored detector."""

from typing import Any

from agentlens.detectors import register
from agentlens.models import PatternInstance, TraceEvent


@register
class ErrorIgnoredDetector:
    """Detect when a tool error is followed by a success claim without retry."""

    pattern_type = "error-ignored"
    severity = "critical"
    deduction = 25

    def detect(
        self, events: list[TraceEvent], config: dict[str, Any] | None = None
    ) -> list[PatternInstance]:
        """Detect ignored errors."""
        instances = []

        for i, event in enumerate(events):
            if event.type == "tool_result" and event.error:
                # Look ahead for the next assistant message
                for j in range(i + 1, len(events)):
                    next_event = events[j]

                    # If we see another tool_call, that's a retry - no violation
                    if next_event.type == "tool_call":
                        break

                    # If we see an assistant message claiming success
                    if next_event.type == "message" and next_event.role == "assistant":
                        content = (next_event.content or "").lower()
                        success_keywords = ["done", "success", "completed"]

                        if any(keyword in content for keyword in success_keywords):
                            instances.append(
                                PatternInstance(
                                    pattern_type=self.pattern_type,
                                    severity=self.severity,
                                    deduction=self.deduction,
                                    details={
                                        "error": event.error,
                                        "claimed_success": next_event.content,
                                    },
                                )
                            )
                        break

        return instances
