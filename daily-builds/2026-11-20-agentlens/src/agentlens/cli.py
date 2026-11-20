"""Command-line interface for agentlens."""

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from agentlens.detectors import get_all_detectors
from agentlens.formatters import format_output
from agentlens.scorer import analyze_trace
from agentlens.trace_loader import load_trace

app = typer.Typer(help="AI Agent Reliability Analyzer")
console = Console()


@app.command()
def analyze(
    trace_file: Annotated[Path, typer.Argument(help="Path to trace JSONL file")],
    format: Annotated[str, typer.Option(help="Output format")] = "cli",
    output: Annotated[Path | None, typer.Option(help="Write output to file")] = None,
    tools: Annotated[Path | None, typer.Option(help="Path to tools catalog JSON")] = None,
    fail_under: Annotated[int, typer.Option(help="Exit 1 if score below this")] = 0,
    verbose: Annotated[bool, typer.Option(help="Show detailed instance info")] = False,
) -> None:
    """Analyze an agent trace for reliability patterns."""
    try:
        # Load trace
        events = load_trace(trace_file)

        # Build config
        config = {"fail_under": fail_under}
        if tools:
            config["tools_catalog"] = str(tools)

        # Analyze
        result = analyze_trace(events, config)

        # Format output
        formatted = format_output(result, format, verbose)

        # Write or print
        if output:
            output.write_text(formatted, encoding="utf-8")
            console.print(f"[green]✓[/green] Analysis written to {output}")
        else:
            console.print(formatted)

        # Exit code
        if result.score < fail_under:
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        sys.exit(1)


@app.command()
def rules(
    format: Annotated[str, typer.Option(help="Output format: table or json")] = "table",
) -> None:
    """List all detection rules."""
    detectors = get_all_detectors()

    if format == "json":
        import json

        rules = []
        for detector_cls in detectors:
            detector = detector_cls()
            rules.append(
                {
                    "pattern_type": detector.pattern_type,
                    "severity": detector.severity,
                    "deduction": detector.deduction,
                }
            )
        console.print(json.dumps(rules, indent=2))

    else:
        table = Table(title="Detection Rules", show_header=True, header_style="bold cyan")
        table.add_column("Pattern", style="dim", width=25)
        table.add_column("Severity", justify="center")
        table.add_column("Deduction", justify="right")

        for detector_cls in detectors:
            detector = detector_cls()
            severity_color = {
                "critical": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "dim",
            }.get(detector.severity, "white")

            table.add_row(
                detector.pattern_type,
                f"[{severity_color}]{detector.severity}[/{severity_color}]",
                f"-{detector.deduction}",
            )

        console.print(table)


@app.command()
def serve(
    port: Annotated[int, typer.Option(help="Port to listen on")] = 8080,
) -> None:
    """Start the FastAPI service."""
    import uvicorn

    console.print(f"[cyan]Starting agentlens API on port {port}...[/cyan]")
    uvicorn.run("agentlens.api:app", host="0.0.0.0", port=port, log_level="info")


def main() -> None:
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
