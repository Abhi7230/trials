"""Tests for trace loader."""

from pathlib import Path

import pytest

from agentlens.trace_loader import load_trace


def test_load_native_trace(tmp_path: Path) -> None:
    """Test loading native format trace."""
    trace_file = tmp_path / "trace.jsonl"
    trace_file.write_text(
        '{"timestamp":"2026-11-20T10:00:00Z","type":"message","role":"user","content":"Hello"}\n'
        '{"timestamp":"2026-11-20T10:00:01Z","type":"tool_call","role":"assistant",'
        '"tool_call_id":"c1","tool_name":"test","tool_args":{"x":1}}\n'
    )

    events = load_trace(trace_file)
    assert len(events) == 2
    assert events[0].type == "message"
    assert events[0].role == "user"
    assert events[1].type == "tool_call"
    assert events[1].tool_name == "test"
    assert events[1].tool_args == {"x": 1}


def test_load_openai_trace(tmp_path: Path) -> None:
    """Test loading OpenAI-style trace."""
    trace_file = tmp_path / "trace.jsonl"
    trace_file.write_text(
        '{"role":"user","content":"Hello","timestamp":"2026-11-20T10:00:00Z"}\n'
        '{"role":"assistant","tool_calls":[{"id":"c1","type":"function",'
        '"function":{"name":"test","arguments":"{\\"x\\":1}"}}],"timestamp":"2026-11-20T10:00:01Z"}\n'
        '{"role":"tool","tool_call_id":"c1","content":"OK","timestamp":"2026-11-20T10:00:02Z"}\n'
    )

    events = load_trace(trace_file)
    assert len(events) == 3
    assert events[0].type == "message"
    assert events[0].role == "user"
    assert events[1].type == "tool_call"
    assert events[1].tool_name == "test"
    assert events[1].tool_args == {"x": 1}
    assert events[2].type == "tool_result"


def test_mixed_schema_rejected(tmp_path: Path) -> None:
    """Test that mixed schemas are rejected."""
    trace_file = tmp_path / "trace.jsonl"
    trace_file.write_text(
        '{"timestamp":"2026-11-20T10:00:00Z","type":"message","role":"user","content":"Hello"}\n'
        '{"role":"assistant","content":"Hi","timestamp":"2026-11-20T10:00:01Z"}\n'
    )

    with pytest.raises(ValueError, match="Mixed schemas"):
        load_trace(trace_file)


def test_malformed_json_error(tmp_path: Path) -> None:
    """Test that malformed JSON gives clear error with line number."""
    trace_file = tmp_path / "trace.jsonl"
    trace_file.write_text(
        '{"timestamp":"t1","type":"message","role":"user","content":"Hi"}\n'
        '{invalid json\n'
    )

    with pytest.raises(ValueError, match="Invalid JSON at line 2"):
        load_trace(trace_file)


def test_empty_file(tmp_path: Path) -> None:
    """Test that empty file returns empty list."""
    trace_file = tmp_path / "trace.jsonl"
    trace_file.write_text("")

    events = load_trace(trace_file)
    assert events == []
