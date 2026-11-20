"""Load and normalize trace events from JSONL."""

import json
from pathlib import Path
from typing import Any

from agentlens.models import TraceEvent


def load_trace(filepath: Path) -> list[TraceEvent]:
    """
    Load a trace from a JSONL file.

    Supports two schemas:
    1. Native: {timestamp, type, role, content, tool_call_id, tool_name, tool_args, ...}
    2. OpenAI-style: messages with tool_calls and tool results

    Raises:
        ValueError: If the file contains mixed schemas or malformed JSON
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Trace file not found: {filepath}")

    with open(filepath, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        return []

    events = []
    detected_schema: str | None = None

    for line_num, line in enumerate(lines, start=1):
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON at line {line_num}: {e}"
            raise ValueError(msg) from e

        # Detect schema
        try:
            current_schema = _detect_schema(raw)
        except ValueError as e:
            # Re-raise with line number
            msg = f"Line {line_num}: {e}"
            raise ValueError(msg) from e

        if detected_schema is None:
            detected_schema = current_schema
        elif detected_schema != current_schema:
            msg = (
                f"Mixed schemas detected: {detected_schema} vs "
                f"{current_schema} at line {line_num}"
            )
            raise ValueError(msg)

        # Parse based on schema
        if current_schema == "native":
            events.append(TraceEvent(**raw))
        elif current_schema == "openai":
            events.extend(_normalize_openai_message(raw))

    return events


def _detect_schema(obj: dict[str, Any]) -> str:
    """Detect if this is a native or OpenAI-style message."""
    if "type" in obj and obj["type"] in ("message", "tool_call", "tool_result"):
        return "native"
    if "role" in obj and obj["role"] in ("user", "assistant", "system", "tool"):
        return "openai"
    msg = f"Unrecognized schema: {obj}"
    raise ValueError(msg)


def _normalize_openai_message(msg: dict[str, Any]) -> list[TraceEvent]:
    """Convert an OpenAI-style message to normalized TraceEvents."""
    events = []
    role = msg["role"]

    if role == "assistant" and "tool_calls" in msg:
        # Assistant message with tool calls
        for tc in msg["tool_calls"]:
            func = tc["function"]
            try:
                args = json.loads(func["arguments"]) if func["arguments"] else {}
            except json.JSONDecodeError:
                args = {}

            events.append(
                TraceEvent(
                    timestamp=msg.get("timestamp", ""),
                    type="tool_call",
                    role="assistant",
                    content=msg.get("content"),
                    tool_call_id=tc["id"],
                    tool_name=func["name"],
                    tool_args=args,
                )
            )
    elif role == "tool":
        # Tool result message
        events.append(
            TraceEvent(
                timestamp=msg.get("timestamp", ""),
                type="tool_result",
                role="tool",
                content=msg.get("content"),
                tool_call_id=msg.get("tool_call_id"),
            )
        )
    else:
        # Regular message (user, assistant without tool calls, system)
        events.append(
            TraceEvent(
                timestamp=msg.get("timestamp", ""),
                type="message",
                role=role,
                content=msg.get("content"),
            )
        )

    return events
