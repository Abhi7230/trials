"""Command-line interface for mcp-probe."""

import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from .runner import ProbeRunner
from .transcript import check_transcript_static
from .report import format_table, format_json, format_markdown

app = typer.Typer(help="MCP Probe - Offline conformance tester for MCP servers")
console = Console()


@app.command()
def run(
    cmd: str = typer.Option(..., "--cmd", help="Command to launch MCP server"),
    timeout: float = typer.Option(5.0, "--timeout", help="Request timeout in seconds"),
    seed: int = typer.Option(1, "--seed", help="Random seed for fuzzing"),
    fuzz_per_tool: int = typer.Option(8, "--fuzz-per-tool", help="Fuzz test cases per tool"),
    format: str = typer.Option("table", "--format", help="Output format: table, json, markdown"),
    fail_under: Optional[float] = typer.Option(None, "--fail-under", help="Fail if score below threshold"),
    out: Optional[str] = typer.Option(None, "--out", help="Write report to file"),
):
    """Run MCP probe against a server."""
    runner = ProbeRunner(cmd, timeout, seed, fuzz_per_tool)
    
    try:
        report = runner.run()
    except Exception as e:
        console.print(f"[red]Error running probe: {e}[/red]")
        raise typer.Exit(1)
    
    if format == "json":
        output = format_json(report)
    elif format == "markdown":
        output = format_markdown(report)
    else:
        output = format_table(report)
    
    if out:
        Path(out).write_text(output)
        console.print(f"Report written to {out}")
    else:
        console.print(output)
    
    if fail_under is not None and report.score < fail_under:
        console.print(f"\n[red]Score {report.score:.1f} is below threshold {fail_under}[/red]")
        raise typer.Exit(1)


@app.command()
def check_transcript(
    transcript_path: str = typer.Argument(..., help="Path to JSONL transcript file"),
    format: str = typer.Option("table", "--format", help="Output format: table, json, markdown"),
    out: Optional[str] = typer.Option(None, "--out", help="Write report to file"),
):
    """Check a recorded transcript offline."""
    try:
        from .models import Report
        report_dict = check_transcript_static(transcript_path)
        report = Report(**report_dict)
    except Exception as e:
        console.print(f"[red]Error checking transcript: {e}[/red]")
        raise typer.Exit(1)
    
    if format == "json":
        output = format_json(report)
    elif format == "markdown":
        output = format_markdown(report)
    else:
        output = format_table(report)
    
    if out:
        Path(out).write_text(output)
        console.print(f"Report written to {out}")
    else:
        console.print(output)


@app.command()
def record(
    cmd: str = typer.Option(..., "--cmd", help="Command to launch MCP server"),
    out: str = typer.Option(..., "--out", help="Output JSONL file"),
):
    """Record an MCP session to transcript (stub - not fully implemented)."""
    console.print("[yellow]Record mode is a stub in this version[/yellow]")
    console.print(f"Would record session from: {cmd}")
    console.print(f"Would write to: {out}")


@app.command()
def rules():
    """List all probe rules."""
    rules_info = [
        ("HS001-HS013", "Handshake", "Protocol handshake conformance"),
        ("TS001-TS011", "Tool Schema", "Tool schema validation"),
        ("RS001-RS007", "Results", "Tool result conformance"),
        ("FZ001-FZ003", "Fuzzing", "Invalid input handling"),
        ("RB001-RB005", "Robustness", "Server stability and performance"),
    ]
    
    console.print("\n[bold]MCP Probe Rules[/bold]\n")
    for rule_id, category, description in rules_info:
        console.print(f"[cyan]{rule_id:12}[/cyan] {category:15} {description}")
    console.print()


@app.command()
def serve(
    port: int = typer.Option(8000, "--port", help="Port to listen on"),
):
    """Start FastAPI server for HTTP API."""
    import uvicorn
    from .api import app as api_app
    
    console.print(f"Starting API server on port {port}...")
    uvicorn.run(api_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    app()
