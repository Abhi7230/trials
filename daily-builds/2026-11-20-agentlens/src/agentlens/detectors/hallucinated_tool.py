"""Hallucinated tool detector."""

import json
from pathlib import Path
from typing import Any

from agentlens.detectors import register
from agentlens.models import PatternInstance, TraceEvent


@register
class HallucinatedToolDetector:
    """Detect tool names not in the catalog."""

    pattern_type = "hallucinated-tool"
    severity = "high"
    deduction = 15

    def detect(
        self, events: list[TraceEvent], config: dict[str, Any] | None = None
    ) -> list[PatternInstance]:
        """Detect hallucinated tools."""
        instances = []
        config = config or {}

        # Skip if no catalog provided
        catalog_path = config.get("tools_catalog")
        if not catalog_path:
            return instances

        # Load catalog
        with open(Path(catalog_path), encoding="utf-8") as f:
            catalog = json.load(f)

        known_tools = set(catalog.get("tools", []))

        # Check all tool calls
        seen_unknown: set[str] = set()
        for event in events:
            if event.type == "tool_call":
                tool_name = event.tool_name
                if tool_name and tool_name not in known_tools and tool_name not in seen_unknown:
                    seen_unknown.add(tool_name)
                    instances.append(
                        PatternInstance(
                            pattern_type=self.pattern_type,
                            severity=self.severity,
                            deduction=self.deduction,
                            details={"tool": tool_name},
                        )
                    )

        return instances
