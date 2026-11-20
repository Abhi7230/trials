"""Latency outlier detector."""

from typing import Any

from agentlens.detectors import register
from agentlens.models import PatternInstance, TraceEvent


@register
class LatencyOutlierDetector:
    """Detect latency outliers."""

    pattern_type = "latency-outlier"
    severity = "low"
    deduction = 5

    def detect(
        self, events: list[TraceEvent], config: dict[str, Any] | None = None
    ) -> list[PatternInstance]:
        """Detect latency outliers."""
        instances = []
        config = config or {}
        single_turn_limit = config.get("latency_single_turn_ms", 10_000)
        p95_limit = config.get("latency_p95_ms", 5_000)

        latencies = []

        for event in events:
            if event.latency_ms:
                latencies.append(event.latency_ms)

                # Check single turn
                if event.latency_ms > single_turn_limit:
                    instances.append(
                        PatternInstance(
                            pattern_type=self.pattern_type,
                            severity=self.severity,
                            deduction=self.deduction,
                            details={"type": "single_turn", "latency_ms": event.latency_ms},
                        )
                    )

        # Check P95
        if latencies:
            sorted_latencies = sorted(latencies)
            p95_idx = int(len(sorted_latencies) * 0.95)
            p95 = sorted_latencies[p95_idx] if p95_idx < len(sorted_latencies) else sorted_latencies[-1]

            if p95 > p95_limit:
                instances.append(
                    PatternInstance(
                        pattern_type=self.pattern_type,
                        severity=self.severity,
                        deduction=self.deduction,
                        details={"type": "p95", "latency_ms": p95},
                    )
                )

        return instances
