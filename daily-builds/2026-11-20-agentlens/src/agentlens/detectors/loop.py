"""Tool call loop detector."""

import difflib
import json
from typing import Any

from agentlens.detectors import register
from agentlens.models import PatternInstance, TraceEvent


@register
class ToolCallLoopDetector:
    """Detect when the same tool is called repeatedly with identical or near-identical args."""

    pattern_type = "tool-call-loop"
    severity = "high"
    deduction = 15

    def detect(
        self, events: list[TraceEvent], config: dict[str, Any] | None = None
    ) -> list[PatternInstance]:
        """Detect tool call loops."""
        instances = []
        config = config or {}
        min_streak = config.get("loop_min_streak", 4)

        # Track consecutive calls to the same tool
        current_tool: str | None = None
        current_args: list[str] = []  # JSON strings for comparison
        streak = 0

        for event in events:
            if event.type == "tool_call":
                tool_name = event.tool_name
                args_str = json.dumps(event.tool_args or {}, sort_keys=True)

                # Check if this continues the streak
                if tool_name == current_tool:
                    # Check if args are identical or nearly identical to any previous call in streak
                    is_similar = False
                    for prev_args in current_args:
                        similarity = difflib.SequenceMatcher(None, args_str, prev_args).ratio()
                        if similarity >= 0.9:
                            is_similar = True
                            break

                    if is_similar:
                        streak += 1
                        current_args.append(args_str)
                    else:
                        # Different args, reset streak
                        if streak >= min_streak:
                            instances.append(
                                PatternInstance(
                                    pattern_type=self.pattern_type,
                                    severity=self.severity,
                                    deduction=self.deduction,
                                    details={"tool": current_tool, "count": streak},
                                )
                            )
                        current_tool = tool_name
                        current_args = [args_str]
                        streak = 1
                else:
                    # Different tool, check if we had a streak
                    if streak >= min_streak:
                        instances.append(
                            PatternInstance(
                                pattern_type=self.pattern_type,
                                severity=self.severity,
                                deduction=self.deduction,
                                details={"tool": current_tool, "count": streak},
                            )
                        )
                    current_tool = tool_name
                    current_args = [args_str]
                    streak = 1

            elif event.type == "message" or (event.type == "tool_result" and not event.error):
                # Non-tool-call event that's not an error result - these can break the loop
                # (Successful tool results are expected and don't break the loop)
                # But only break if it's not a tool_result at all, or it's a success
                # We want to allow tool_result errors to continue the loop context
                pass  # Don't reset on tool_result - let it continue

        # Check final streak
        if streak >= min_streak:
            instances.append(
                PatternInstance(
                    pattern_type=self.pattern_type,
                    severity=self.severity,
                    deduction=self.deduction,
                    details={"tool": current_tool, "count": streak},
                )
            )

        return instances
