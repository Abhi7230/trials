"""Command-line interface."""

import json
import sys

import typer
import uvicorn
from rich.console import Console

from agent_ledger.db import get_connection, init_db
from agent_ledger.invariants import InvariantChecker
from agent_ledger.replay import replay_file
from agent_ledger.tools import generate_tool_manifest

app = typer.Typer(help="Agent Ledger CLI")
console = Console()


@app.command()
def serve(
    db: str = typer.Option("ledger.db", help="Database path"),
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
):
    """Start the FastAPI server."""
    # Import here to avoid circular dependency
    from agent_ledger.app import create_app
    
    # Initialize database
    conn = get_connection(db)
    init_db(conn)
    conn.close()
    
    # Set environment variable for the app to use
    import os
    os.environ["AGENT_LEDGER_DB"] = db
    
    uvicorn.run(
        "agent_ledger.app:create_app",
        host=host,
        port=port,
        factory=True,
        log_level="info",
    )


@app.command()
def replay(
    scenario: str = typer.Argument(..., help="Path to scenario file (YAML or JSONL)"),
    db: str = typer.Option(":memory:", help="Database path"),
    format: str = typer.Option("text", help="Output format (text or json)"),
):
    """Replay a scenario file."""
    exit_code = replay_file(scenario, db, format)
    sys.exit(exit_code)


@app.command()
def check(
    db: str = typer.Option("ledger.db", help="Database path"),
):
    """Check ledger invariants."""
    conn = get_connection(db)
    checker = InvariantChecker(conn)
    result = checker.check_all()
    
    if result["ok"]:
        console.print("[green]✓ All invariants passed[/green]")
        sys.exit(0)
    else:
        console.print("[red]✗ Invariant violations found:[/red]")
        for violation in result["violations"]:
            console.print(f"  {violation['type']}: {violation['description']}")
            console.print(f"    Details: {violation['details']}")
        sys.exit(1)


@app.command()
def tools():
    """Print tool manifest JSON."""
    manifest = generate_tool_manifest()
    print(json.dumps(manifest, indent=2))


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
