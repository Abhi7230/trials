"""Scoring and grading logic."""

from .models import Finding, Severity


SEVERITY_WEIGHTS = {
    Severity.ERROR: -10,
    Severity.WARNING: -3,
    Severity.INFO: 0,
}


def calculate_score(findings: list[Finding]) -> tuple[float, str]:
    """Calculate score (0-100) and grade (A-F) from findings."""
    score = 100.0
    
    for finding in findings:
        weight = SEVERITY_WEIGHTS.get(finding.severity, 0)
        score += weight
    
    score = max(0.0, min(100.0, score))
    
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"
    
    return score, grade
