"""Tests for reporters."""

import json
from pathlib import Path

from skill_lint.models import Finding, Report, Score, Severity, Skill
from skill_lint.reporters import format_json, format_sarif, format_text


def test_text_reporter() -> None:
    """Test text reporter."""
    skill = Skill(
        path=Path("test.md"),
        name="test",
        description="test skill for reporters when you need testing",
        body="content",
    )
    finding = Finding(
        rule_id="SL001",
        severity=Severity.ERROR,
        message="Test error",
        line=1,
    )
    score = Score(value=85, grade="B", findings_count=1, errors=1, warnings=0, info=0)
    
    report = Report(
        skills=[skill],
        findings={"test.md": [finding]},
        scores={"test.md": score},
        summary={"total_skills": 1, "total_findings": 1, "average_score": 85},
    )
    
    output = format_text(report, use_color=False)
    
    assert "SKILL-LINT REPORT" in output
    assert "test" in output
    assert "85/100" in output
    assert "Test error" in output


def test_json_reporter() -> None:
    """Test JSON reporter."""
    skill = Skill(
        path=Path("test.md"),
        name="test",
        description="test skill for reporters when you need testing",
        body="content",
    )
    finding = Finding(
        rule_id="SL001",
        severity=Severity.ERROR,
        message="Test error",
        line=1,
    )
    score = Score(value=85, grade="B", findings_count=1, errors=1, warnings=0, info=0)
    
    report = Report(
        skills=[skill],
        findings={"test.md": [finding]},
        scores={"test.md": score},
        summary={"total_skills": 1, "total_findings": 1, "average_score": 85},
    )
    
    output = format_json(report)
    data = json.loads(output)
    
    assert "version" in data
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "test"


def test_sarif_reporter() -> None:
    """Test SARIF reporter."""
    skill = Skill(
        path=Path("test.md"),
        name="test",
        description="test skill for reporters when you need testing",
        body="content",
    )
    finding = Finding(
        rule_id="SL001",
        severity=Severity.ERROR,
        message="Test error",
        line=5,
    )
    
    report = Report(
        skills=[skill],
        findings={"test.md": [finding]},
        scores={},
        summary={},
    )
    
    output = format_sarif(report)
    data = json.loads(output)
    
    assert data["version"] == "2.1.0"
    assert "runs" in data
    assert len(data["runs"]) == 1
    assert data["runs"][0]["tool"]["driver"]["name"] == "skill-lint"
    assert len(data["runs"][0]["results"]) == 1
    assert data["runs"][0]["results"][0]["ruleId"] == "SL001"
