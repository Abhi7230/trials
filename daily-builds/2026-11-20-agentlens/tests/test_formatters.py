"""Tests for formatters."""

import json

from agentlens.formatters import format_cli, format_json, format_markdown
from agentlens.models import AnalysisResult


def test_cli_contains_score() -> None:
    """Test CLI formatter contains the score."""
    result = AnalysisResult(
        score=75,
        passed=True,
        patterns=[],
        stats={
            "total_turns": 5,
            "tool_calls": 2,
            "errors": 0,
            "cost_usd": 0.01,
            "duration_ms": 100,
        },
    )

    output = format_cli(result)
    assert "75" in output
    assert "Reliability Score" in output


def test_json_has_score_patterns_stats() -> None:
    """Test JSON formatter has all required fields."""
    result = AnalysisResult(
        score=85,
        passed=True,
        patterns=[
            {
                "type": "test-pattern",
                "severity": "low",
                "count": 1,
                "deduction": 5,
                "instances": [
                    {
                        "pattern_type": "test-pattern",
                        "severity": "low",
                        "deduction": 5,
                        "details": {},
                    }
                ],
            }
        ],
        stats={
            "total_turns": 3,
            "tool_calls": 1,
            "errors": 0,
            "cost_usd": 0.005,
            "duration_ms": 50,
        },
    )

    output = format_json(result)
    parsed = json.loads(output)

    assert parsed["score"] == 85
    assert parsed["passed"] is True
    assert len(parsed["patterns"]) == 1
    assert "stats" in parsed
    assert parsed["stats"]["total_turns"] == 3


def test_markdown_has_table_header() -> None:
    """Test Markdown formatter has the table header."""
    result = AnalysisResult(
        score=90,
        passed=True,
        patterns=[],
        stats={
            "total_turns": 2,
            "tool_calls": 0,
            "errors": 0,
            "cost_usd": 0.0,
            "duration_ms": 20,
        },
    )

    output = format_markdown(result)
    assert "| Pattern | Severity | Count | Deduction |" in output or "## Statistics" in output
    assert "**Score:** 90/100" in output
