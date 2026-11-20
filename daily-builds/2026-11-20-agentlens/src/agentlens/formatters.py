"""Output formatters for analysis results."""

import json

from rich.console import Console
from rich.table import Table

from agentlens.models import AnalysisResult


def format_cli(result: AnalysisResult, verbose: bool = False) -> str:
    """Format result as rich CLI output."""
    console = Console(record=True, width=100)

    # Score with color
    score = result.score
    if score >= 80:
        color = "green"
    elif score >= 50:
        color = "yellow"
    else:
        color = "red"

    console.print(f"\n[bold]Reliability Score:[/bold] [{color}]{score}/100[/{color}]")
    console.print()

    # Patterns table
    if result.patterns:
        table = Table(title="Detected Patterns", show_header=True, header_style="bold cyan")
        table.add_column("Pattern", style="dim", width=25)
        table.add_column("Severity", justify="center")
        table.add_column("Count", justify="right")
        table.add_column("Deduction", justify="right")

        for pattern in result.patterns:
            severity_color = {
                "critical": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "dim",
            }.get(pattern["severity"], "white")

            table.add_row(
                pattern["type"],
                f"[{severity_color}]{pattern['severity']}[/{severity_color}]",
                str(pattern["count"]),
                f"-{pattern['deduction']}",
            )

        console.print(table)
        console.print()

    # Stats
    stats = result.stats
    console.print("[bold]Statistics:[/bold]")
    console.print(f"  Total turns: {stats['total_turns']}")
    console.print(f"  Tool calls: {stats['tool_calls']}")
    console.print(f"  Errors: {stats['errors']}")
    console.print(f"  Cost: ${stats['cost_usd']:.4f}")
    console.print(f"  Duration: {stats['duration_ms']:.2f} ms")
    console.print()

    # Verbose: show instance details
    if verbose and result.patterns:
        console.print("[bold]Details:[/bold]")
        for pattern in result.patterns:
            console.print(f"\n[cyan]{pattern['type']}[/cyan] ({pattern['count']} instances):")
            for inst in pattern["instances"]:
                details = inst.get("details", {})
                console.print(f"  • {details}")

    return console.export_text()


def format_json(result: AnalysisResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.model_dump(), indent=2)


def format_markdown(result: AnalysisResult) -> str:
    """Format result as Markdown."""
    lines = [
        "# Agent Reliability Analysis",
        "",
        f"**Score:** {result.score}/100",
        "",
    ]

    if result.patterns:
        lines.extend(
            [
                "## Detected Patterns",
                "",
                "| Pattern | Severity | Count | Deduction |",
                "|---------|----------|-------|-----------|",
            ]
        )

        for pattern in result.patterns:
            p_type = pattern["type"]
            p_sev = pattern["severity"]
            p_count = pattern["count"]
            p_deduct = pattern["deduction"]
            lines.append(f"| {p_type} | {p_sev} | {p_count} | -{p_deduct} |")

        lines.append("")

        # Add details
        lines.append("## Findings")
        lines.append("")
        for pattern in result.patterns:
            lines.append(f"### {pattern['type']}")
            lines.append("")
            for inst in pattern["instances"]:
                details = inst.get("details", {})
                lines.append(f"- {details}")
            lines.append("")

    # Stats
    stats = result.stats
    lines.extend(
        [
            "## Statistics",
            "",
            f"- **Total turns:** {stats['total_turns']}",
            f"- **Tool calls:** {stats['tool_calls']}",
            f"- **Errors:** {stats['errors']}",
            f"- **Cost:** ${stats['cost_usd']:.4f}",
            f"- **Duration:** {stats['duration_ms']:.2f} ms",
            "",
        ]
    )

    return "\n".join(lines)


def format_output(
    result: AnalysisResult, format_type: str = "cli", verbose: bool = False
) -> str:
    """Format result based on type."""
    if format_type == "json":
        return format_json(result)
    if format_type == "markdown":
        return format_markdown(result)
    return format_cli(result, verbose)
