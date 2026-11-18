"""Tests for scoring module."""

from skill_lint.models import Finding, Severity
from skill_lint.scoring import calculate_score


def test_perfect_score() -> None:
    """Test scoring with no findings."""
    score = calculate_score([])
    
    assert score.value == 100
    assert score.grade == "A"
    assert score.findings_count == 0


def test_score_with_errors() -> None:
    """Test scoring with error findings."""
    findings = [
        Finding(rule_id="SL001", severity=Severity.ERROR, message="test"),
        Finding(rule_id="SL002", severity=Severity.ERROR, message="test"),
    ]
    
    score = calculate_score(findings)
    
    assert score.value == 70  # 100 - 2*15
    assert score.grade == "C"
    assert score.errors == 2


def test_score_with_warnings() -> None:
    """Test scoring with warning findings."""
    findings = [
        Finding(rule_id="SL003", severity=Severity.WARNING, message="test"),
        Finding(rule_id="SL004", severity=Severity.WARNING, message="test"),
    ]
    
    score = calculate_score(findings)
    
    assert score.value == 90  # 100 - 2*5
    assert score.grade == "A"
    assert score.warnings == 2


def test_score_with_mixed_findings() -> None:
    """Test scoring with mixed severity findings."""
    findings = [
        Finding(rule_id="SL001", severity=Severity.ERROR, message="test"),
        Finding(rule_id="SL003", severity=Severity.WARNING, message="test"),
        Finding(rule_id="SL004", severity=Severity.INFO, message="test"),
    ]
    
    score = calculate_score(findings)
    
    # 100 - 15 (error) - 5 (warning) - 2 (info) = 78
    assert score.value == 78
    assert score.grade == "C"


def test_score_grade_boundaries() -> None:
    """Test grade assignment at boundaries."""
    assert calculate_score([]).grade == "A"  # 100
    
    # 85 = B (100 - 3*5)
    findings_b = [Finding(rule_id="SL003", severity=Severity.WARNING, message="test")] * 3
    assert calculate_score(findings_b).grade == "B"
    
    # 75 = C (100 - 5*5)
    findings_c = [Finding(rule_id="SL003", severity=Severity.WARNING, message="test")] * 5
    assert calculate_score(findings_c).grade == "C"
