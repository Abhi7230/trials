#!/usr/bin/env python3
"""Generate demo screenshot for README."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from mcp_probe.runner import ProbeRunner
from mcp_probe.report.table import format_table
from mcp_probe.models import Report
from rich.console import Console

fixtures_dir = project_root / "fixtures"
docs_dir = project_root / "docs"
docs_dir.mkdir(exist_ok=True)


def main():
    """Generate demo by running against buggy server."""
    print("Running mcp-probe against buggy_server...")
    
    runner = ProbeRunner(
        cmd=f"{sys.executable} {fixtures_dir / 'buggy_server.py'}",
        timeout=2.0,
        seed=1,
        fuzz_per_tool=2
    )
    
    report = runner.run()
    
    console = Console(record=True, width=120)
    
    console.print(f"\n[bold cyan]MCP Probe Report[/bold cyan]")
    console.print(f"[yellow]Score:[/yellow] [bold]{report.score:.1f}/100[/bold] ([bold]Grade: {report.grade}[/bold])")
    
    if report.server_info:
        server_info = report.server_info.get("serverInfo", {})
        console.print(f"[yellow]Server:[/yellow] {server_info.get('name', 'unknown')} v{server_info.get('version', 'unknown')}")
    
    console.print(f"[yellow]Tools:[/yellow] {report.stats.get('tool_count', 0)}")
    console.print(f"[yellow]Tests:[/yellow] {report.stats.get('test_count', 0)}")
    console.print(f"[yellow]Latency:[/yellow] p50={report.stats.get('latency_p50', 0):.3f}s, p95={report.stats.get('latency_p95', 0):.3f}s\n")
    
    if report.findings[:10]:
        from rich.table import Table
        table = Table(title="Findings (Top 10)")
        table.add_column("Severity", style="bold", width=10)
        table.add_column("Rule ID", width=10)
        table.add_column("Message", width=70)
        
        severity_styles = {
            "error": "red",
            "warning": "yellow",
            "info": "blue",
        }
        
        for finding in report.findings[:10]:
            style = severity_styles.get(finding.severity, "")
            table.add_row(
                f"[{style}]{finding.severity.upper()}[/{style}]",
                finding.rule_id,
                finding.message[:70],
            )
        
        console.print(table)
    
    svg_path = docs_dir / "demo.svg"
    console.save_svg(str(svg_path), title="MCP Probe Demo")
    print(f"Saved SVG to {svg_path}")
    
    try:
        import cairosvg
        png_path = docs_dir / "demo.png"
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), scale=2.0)
        print(f"Saved PNG to {png_path}")
    except ImportError:
        print("cairosvg not available, PNG not generated")
        print("SVG saved, you can manually convert it or install cairosvg")


if __name__ == "__main__":
    main()
