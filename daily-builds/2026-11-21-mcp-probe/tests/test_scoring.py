"""Tests for scoring."""

import pytest
from mcp_probe.models import Finding, Severity
from mcp_probe.scoring import calculate_score


def test_perfect_score():
    """Test perfect score with no findings."""
    findings = []
    score, grade = calculate_score(findings)
    assert score == 100.0
    assert grade == "A"


def test_score_with_errors():
    """Test score decreases with errors."""
    findings = [
        Finding(rule_id="TEST001", severity=Severity.ERROR, message="Error 1"),
        Finding(rule_id="TEST002", severity=Severity.ERROR, message="Error 2"),
    ]
    
    score, grade = calculate_score(findings)
    assert score == 80.0
    assert grade == "B"


def test_score_with_warnings():
    """Test score decreases with warnings."""
    findings = [
        Finding(rule_id="TEST001", severity=Severity.WARNING, message="Warning 1"),
        Finding(rule_id="TEST002", severity=Severity.WARNING, message="Warning 2"),
    ]
    
    score, grade = calculate_score(findings)
    assert score == 94.0
    assert grade == "A"


def test_score_with_info():
    """Test info findings don't affect score."""
    findings = [
        Finding(rule_id="TEST001", severity=Severity.INFO, message="Info 1"),
        Finding(rule_id="TEST002", severity=Severity.INFO, message="Info 2"),
    ]
    
    score, grade = calculate_score(findings)
    assert score == 100.0
    assert grade == "A"


def test_score_mixed_severity():
    """Test mixed severity findings."""
    findings = [
        Finding(rule_id="TEST001", severity=Severity.ERROR, message="Error"),
        Finding(rule_id="TEST002", severity=Severity.WARNING, message="Warning"),
        Finding(rule_id="TEST003", severity=Severity.INFO, message="Info"),
    ]
    
    score, grade = calculate_score(findings)
    assert score == 87.0
    assert grade == "B"


def test_grade_thresholds():
    """Test grade calculation thresholds."""
    assert calculate_score([Finding(rule_id="T", severity=Severity.ERROR, message="E")] * 1)[1] == "A"
    assert calculate_score([Finding(rule_id="T", severity=Severity.ERROR, message="E")] * 2)[1] == "B"
    assert calculate_score([Finding(rule_id="T", severity=Severity.ERROR, message="E")] * 3)[1] == "C"
    assert calculate_score([Finding(rule_id="T", severity=Severity.ERROR, message="E")] * 4)[1] == "D"
    assert calculate_score([Finding(rule_id="T", severity=Severity.ERROR, message="E")] * 11)[1] == "F"


def test_score_minimum():
    """Test score doesn't go below 0."""
    findings = [Finding(rule_id="T", severity=Severity.ERROR, message="E")] * 100
    score, grade = calculate_score(findings)
    assert score == 0.0
    assert grade == "F"
