"""Rich table formatter."""

from rich.console import Console
from rich.table import Table
from ..models import Report, Severity


def format_table(report: Report) -> str:
    """Format report as rich table."""
    console = Console(record=True, width=120)
    
    console.print(f"\n[bold]MCP Probe Report[/bold]")
    console.print(f"Score: [bold]{report.score:.1f}/100[/bold] (Grade: {report.grade})")
    
    if report.server_info:
        server_info = report.server_info.get("serverInfo", {})
        console.print(f"Server: {server_info.get('name', 'unknown')} v{server_info.get('version', 'unknown')}")
    
    console.print(f"Tools: {report.stats.get('tool_count', 0)}")
    console.print(f"Tests: {report.stats.get('test_count', 0)}")
    console.print(f"Latency: p50={report.stats.get('latency_p50', 0):.3f}s, p95={report.stats.get('latency_p95', 0):.3f}s\n")
    
    if report.findings:
        table = Table(title="Findings")
        table.add_column("Severity", style="bold")
        table.add_column("Rule ID")
        table.add_column("Message")
        table.add_column("Location")
        
        severity_styles = {
            Severity.ERROR: "red",
            Severity.WARNING: "yellow",
            Severity.INFO: "blue",
        }
        
        for finding in report.findings:
            style = severity_styles.get(finding.severity, "")
            table.add_row(
                f"[{style}]{finding.severity.upper()}[/{style}]",
                finding.rule_id,
                finding.message,
                finding.location or "-",
            )
        
        console.print(table)
    else:
        console.print("[green]✓ No issues found![/green]")
    
    return console.export_text()
