"""Scoring system for skill quality."""

from .models import Finding, Score, Severity


def calculate_score(findings: list[Finding]) -> Score:
    """Calculate quality score from findings.
    
    Args:
        findings: List of findings
        
    Returns:
        Score object with value 0-100 and letter grade
    """
    # Count findings by severity
    errors = sum(1 for f in findings if f.severity == Severity.ERROR)
    warnings = sum(1 for f in findings if f.severity == Severity.WARNING)
    info = sum(1 for f in findings if f.severity == Severity.INFO)
    
    # Calculate deductions (weighted by severity)
    error_penalty = errors * 15
    warning_penalty = warnings * 5
    info_penalty = info * 2
    
    total_penalty = error_penalty + warning_penalty + info_penalty
    score_value = max(0, 100 - total_penalty)
    
    # Assign letter grade
    if score_value >= 90:
        grade = "A"
    elif score_value >= 80:
        grade = "B"
    elif score_value >= 70:
        grade = "C"
    elif score_value >= 60:
        grade = "D"
    else:
        grade = "F"
    
    return Score(
        value=score_value,
        grade=grade,
        findings_count=len(findings),
        errors=errors,
        warnings=warnings,
        info=info,
    )
