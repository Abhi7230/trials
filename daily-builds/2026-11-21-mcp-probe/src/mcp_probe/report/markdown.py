"""Markdown formatter."""

from ..models import Report, Severity


def format_markdown(report: Report) -> str:
    """Format report as Markdown."""
    lines = ["# MCP Probe Report\n"]
    
    lines.append(f"**Score:** {report.score:.1f}/100 (Grade: {report.grade})\n")
    
    if report.server_info:
        server_info = report.server_info.get("serverInfo", {})
        lines.append(f"**Server:** {server_info.get('name', 'unknown')} v{server_info.get('version', 'unknown')}\n")
    
    lines.append(f"**Tools:** {report.stats.get('tool_count', 0)}")
    lines.append(f"**Tests:** {report.stats.get('test_count', 0)}")
    lines.append(f"**Latency:** p50={report.stats.get('latency_p50', 0):.3f}s, p95={report.stats.get('latency_p95', 0):.3f}s\n")
    
    if report.findings:
        lines.append("## Findings\n")
        lines.append("| Severity | Rule ID | Message | Location |")
        lines.append("|----------|---------|---------|----------|")
        
        for finding in report.findings:
            location = finding.location or "-"
            lines.append(f"| {finding.severity.upper()} | {finding.rule_id} | {finding.message} | {location} |")
    else:
        lines.append("✓ No issues found!\n")
    
    return "\n".join(lines)
