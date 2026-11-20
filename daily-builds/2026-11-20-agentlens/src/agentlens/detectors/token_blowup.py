"""Token blowup detector."""

from typing import Any

from agentlens.detectors import register
from agentlens.models import PatternInstance, TraceEvent


@register
class TokenBlowupDetector:
    """Detect excessive token usage."""

    pattern_type = "token-blowup"
    severity = "medium"
    deduction = 10

    def detect(
        self, events: list[TraceEvent], config: dict[str, Any] | None = None
    ) -> list[PatternInstance]:
        """Detect token blowup."""
        instances = []
        config = config or {}
        cumulative_limit = config.get("token_cumulative_limit", 100_000)
        single_turn_limit = config.get("token_single_turn_limit", 50_000)

        cumulative_tokens = 0

        for event in events:
            prompt_tokens = event.prompt_tokens or 0
            completion_tokens = event.completion_tokens or 0
            turn_tokens = prompt_tokens + completion_tokens

            cumulative_tokens += turn_tokens

            # Check single turn
            if turn_tokens > single_turn_limit:
                instances.append(
                    PatternInstance(
                        pattern_type=self.pattern_type,
                        severity=self.severity,
                        deduction=self.deduction,
                        details={"type": "single_turn", "tokens": turn_tokens},
                    )
                )

        # Check cumulative
        if cumulative_tokens > cumulative_limit:
            instances.append(
                PatternInstance(
                    pattern_type=self.pattern_type,
                    severity=self.severity,
                    deduction=self.deduction,
                    details={"type": "cumulative", "tokens": cumulative_tokens},
                )
            )

        return instances
