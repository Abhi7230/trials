"""Plain text reporter."""

from ..models import Report, Severity


def format_text(report: Report, use_color: bool = True) -> str:
    """Format report as plain text.
    
    Args:
        report: Linting report
        use_color: Whether to use ANSI colors
        
    Returns:
        Formatted text
    """
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append("SKILL-LINT REPORT")
    lines.append("=" * 80)
    lines.append("")
    
    # Per-skill results
    for skill in report.skills:
        path = str(skill.path)
        findings = report.findings.get(path, [])
        score = report.scores.get(path)
        
        # Skill header
        skill_name = skill.name or path
        lines.append(f"\n{skill_name}")
        lines.append("-" * len(skill_name))
        
        if score:
            grade_color = _get_grade_color(score.grade, use_color)
            lines.append(
                f"Score: {score.value}/100 ({grade_color}{score.grade}\x1b[0m)" 
                if use_color else f"Score: {score.value}/100 ({score.grade})"
            )
            lines.append(
                f"Findings: {score.errors} errors, "
                f"{score.warnings} warnings, {score.info} info"
            )
        
        # Findings
        if findings:
            lines.append("\nFindings:")
            for finding in findings:
                severity_str = _format_severity(finding.severity, use_color)
                location = f"line {finding.line}" if finding.line else "file"
                lines.append(
                    f"  [{severity_str}] {finding.rule_id}: {finding.message} ({location})"
                )
        else:
            lines.append("\nNo issues found!")
        
        lines.append("")
    
    # Summary
    lines.append("=" * 80)
    lines.append("SUMMARY")
    lines.append("=" * 80)
    summary = report.summary
    lines.append(f"Total skills: {summary['total_skills']}")
    lines.append(f"Total findings: {summary['total_findings']}")
    lines.append(f"Average score: {summary['average_score']}/100")
    
    if summary.get("critiques"):
        lines.append("\nCRITIQUES:")
        for path, critique in summary["critiques"].items():
            lines.append(f"  {path}: {critique}")
    
    lines.append("")
    
    return "\n".join(lines)


def _get_grade_color(grade: str, use_color: bool) -> str:
    """Get ANSI color code for grade."""
    if not use_color:
        return ""
    
    colors = {
        "A": "\x1b[32m",  # Green
        "B": "\x1b[36m",  # Cyan
        "C": "\x1b[33m",  # Yellow
        "D": "\x1b[31m",  # Red
        "F": "\x1b[31;1m",  # Bold red
    }
    return colors.get(grade, "")


def _format_severity(severity: Severity, use_color: bool) -> str:
    """Format severity with optional color."""
    if not use_color:
        return severity.value.upper()
    
    colors = {
        Severity.ERROR: "\x1b[31m",  # Red
        Severity.WARNING: "\x1b[33m",  # Yellow
        Severity.INFO: "\x1b[36m",  # Cyan
    }
    color = colors.get(severity, "")
    return f"{color}{severity.value.upper()}\x1b[0m"
