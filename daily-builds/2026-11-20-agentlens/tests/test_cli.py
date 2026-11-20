"""Tests for CLI."""

import json
from pathlib import Path

from typer.testing import CliRunner

from agentlens.cli import app

runner = CliRunner()


def test_good_trace_exits_0(tmp_path: Path) -> None:
    """Test that good trace exits 0."""
    trace_file = tmp_path / "trace.jsonl"
    trace_file.write_text(
        '{"timestamp":"t1","type":"message","role":"user","content":"Hello"}\n'
    )

    result = runner.invoke(app, ["analyze", str(trace_file)])
    assert result.exit_code == 0


def test_bad_trace_fail_under_exits_1(tmp_path: Path) -> None:
    """Test that bad trace with --fail-under exits 1."""
    trace_file = tmp_path / "trace.jsonl"
    trace_file.write_text(
        '{"timestamp":"t1","type":"tool_result","role":"tool","error":"Failed"}\n'
        '{"timestamp":"t2","type":"message","role":"assistant","content":"Done!"}\n'
    )

    result = runner.invoke(app, ["analyze", str(trace_file), "--fail-under", "80"])
    assert result.exit_code == 1


def test_rules_lists_patterns() -> None:
    """Test that rules command lists patterns."""
    result = runner.invoke(app, ["rules"])
    assert result.exit_code == 0
    assert "tool-call-loop" in result.stdout
    assert "error-ignored" in result.stdout


def test_output_writes_json(tmp_path: Path) -> None:
    """Test --output writes valid JSON."""
    trace_file = tmp_path / "trace.jsonl"
    trace_file.write_text(
        '{"timestamp":"t1","type":"message","role":"user","content":"Hello"}\n'
    )

    output_file = tmp_path / "output.json"
    result = runner.invoke(
        app, ["analyze", str(trace_file), "--format", "json", "--output", str(output_file)]
    )

    assert result.exit_code == 0
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    assert "score" in data
    assert "patterns" in data
