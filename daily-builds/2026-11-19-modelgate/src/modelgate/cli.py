"""Command-line interface."""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from modelgate.catalog import Catalog, Model
from modelgate.config import load_config
from modelgate.policies import get_policy
from modelgate.router import NoRouteError, Router, RoutingRequest
from modelgate.simulate import Simulator, format_results_json, format_results_table
from modelgate.tokens import SimpleTokenizer

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def serve(
    config: Path = typer.Option(Path("models.yaml"), help="Config file"),
    port: int = typer.Option(8080, help="Port to listen on"),
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
) -> None:
    """Start the gateway server."""
    import uvicorn

    from modelgate import api

    # Load config to validate
    try:
        cfg = load_config(config)
        console.print(f"[green]✓[/] Loaded config with {len(cfg.models)} models")
        api.CONFIG_PATH = config
    except Exception as e:
        console.print(f"[red]Error loading config:[/] {e}")
        raise typer.Exit(2) from e

    console.print(f"[blue]Starting server on {host}:{port}[/]")
    uvicorn.run("modelgate.api:app", host=host, port=port, log_level="info")


@app.command()
def models(
    config: Path = typer.Option(Path("models.yaml"), help="Config file"),
) -> None:
    """List available models."""
    try:
        cfg = load_config(config)
        catalog = Catalog([Model.from_config(m) for m in cfg.models])
    except Exception as e:
        console.print(f"[red]Error loading config:[/] {e}")
        raise typer.Exit(2) from e

    table = Table(title="Available Models")
    table.add_column("ID", style="cyan")
    table.add_column("Provider", style="green")
    table.add_column("Cost ($/1M in)", justify="right")
    table.add_column("Cost ($/1M out)", justify="right")
    table.add_column("Latency (ms)", justify="right")
    table.add_column("Context", justify="right")
    table.add_column("Quality", justify="center")
    table.add_column("Capabilities")

    for model in catalog.all():
        table.add_row(
            model.id,
            model.provider,
            f"${model.cost_per_1m_input:.2f}",
            f"${model.cost_per_1m_output:.2f}",
            f"{model.avg_latency_ms:.0f}",
            f"{model.context_window:,}",
            "★" * model.quality_tier,
            ", ".join(sorted(model.capabilities)) or "—",
        )

    console.print(table)


@app.command()
def route(
    prompt: str = typer.Argument(..., help="Prompt text to route"),
    config: Path = typer.Option(Path("models.yaml"), help="Config file"),
    policy: str = typer.Option("balanced", help="Routing policy"),
) -> None:
    """Dry-run routing for a prompt."""
    try:
        cfg = load_config(config)
        catalog = Catalog([Model.from_config(m) for m in cfg.models])
        tokenizer = SimpleTokenizer()
        router = Router(catalog, tokenizer, default_policy=policy)

        request = RoutingRequest(
            model="auto",
            messages=[{"role": "user", "content": prompt}],
            policy_override=policy,
        )

        candidates = router.route(request)

        console.print(f"\n[blue]Routing with policy:[/] {policy}")
        console.print(f"[blue]Prompt:[/] {prompt[:80]}...")

        table = Table(title="Ranked Candidates")
        table.add_column("Rank", justify="right")
        table.add_column("Model", style="cyan")
        table.add_column("Est. Cost", justify="right")
        table.add_column("Latency", justify="right")
        table.add_column("Quality")

        input_tokens = tokenizer.estimate(prompt)
        output_tokens = 500

        for i, model in enumerate(candidates[:5], 1):
            cost = model.blended_cost(input_tokens, output_tokens)
            table.add_row(
                str(i),
                model.id,
                f"${cost:.6f}",
                f"{model.avg_latency_ms:.0f}ms",
                "★" * model.quality_tier,
            )

        console.print(table)

    except NoRouteError as e:
        console.print(f"[red]No route:[/] {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(2) from e


@app.command()
def simulate(
    trace: Path = typer.Argument(..., help="Trace file (JSONL)"),
    config: Path = typer.Option(Path("models.yaml"), help="Config file"),
    policy: list[str] = typer.Option(
        ["cheapest", "balanced"], help="Policies to compare (multiple allowed)"
    ),
    format: str = typer.Option("table", help="Output format: table, json, or svg"),
) -> None:
    """Simulate trace replay across policies."""
    try:
        cfg = load_config(config)
        catalog = Catalog([Model.from_config(m) for m in cfg.models])
        simulator = Simulator(catalog)

        console.print(f"[blue]Loading trace from:[/] {trace}")
        trace_data = simulator.load_trace(trace)
        console.print(f"[green]✓[/] Loaded {len(trace_data)} requests")

        console.print(f"[blue]Simulating policies:[/] {', '.join(policy)}")
        results = simulator.compare_policies(policy, trace_data)

        if format == "json":
            print(format_results_json(results))
        elif format == "svg":
            # For SVG, we'll render the table and export
            console.print("[yellow]SVG output requires rich rendering[/]")
            console.print(format_results_table(results))
        else:
            console.print(format_results_table(results))

    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(2) from e


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
