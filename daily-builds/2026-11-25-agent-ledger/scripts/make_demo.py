#!/usr/bin/env python3
"""Generate demo PNG from scenario replays."""

import sys
from pathlib import Path

from rich.console import Console

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_ledger.replay import ScenarioReplay


def main():
    """Generate demo image."""
    console = Console(record=True, width=120)
    
    # Run dinner scenario
    console.print("\n[bold blue]═══ Dinner Bill Split Scenario ═══[/bold blue]\n")
    
    replayer = ScenarioReplay(":memory:")
    scenario = replayer.load_scenario("examples/dinner.yaml")
    result = replayer.replay(scenario)
    
    # Print key results
    split_result = None
    for r in result["results"]:
        if r["path"] == "/v1/splits":
            split_result = r["response"]
            break
    
    if split_result:
        console.print(f"[green]✓ Items total: ${split_result['items_total_cents'] / 100:.2f}[/green]")
        console.print(f"[green]✓ Tax (8.875%): ${split_result['tax_cents'] / 100:.2f}[/green]")
        console.print(f"[green]✓ Tip (18%): ${split_result['tip_cents'] / 100:.2f}[/green]")
        console.print(f"[green]✓ Grand total: ${split_result['grand_total_cents'] / 100:.2f}[/green]")
        console.print("\n[bold]Shares:[/bold]")
        for share in split_result["shares"]:
            console.print(
                f"  {share['participant']:8} → ${share['total_cents'] / 100:7.2f} "
                f"(items: ${share['items_cents'] / 100:.2f}, "
                f"shared: ${share['shared_cents'] / 100:.2f}, "
                f"tax: ${share['tax_cents'] / 100:.2f}, "
                f"tip: ${share['tip_cents'] / 100:.2f})"
            )
    
    # Run policy walkthrough
    console.print("\n\n[bold blue]═══ Policy Walkthrough ═══[/bold blue]\n")
    
    replayer2 = ScenarioReplay(":memory:")
    scenario2 = replayer2.load_scenario("examples/policy_walkthrough.yaml")
    result2 = replayer2.replay(scenario2)
    
    console.print(f"[yellow]Steps executed: {len(result2['results'])}[/yellow]")
    console.print(f"[yellow]Failures: {len(result2['failures'])}[/yellow]")
    
    # Invariants
    console.print("\n[bold blue]═══ Invariant Check ═══[/bold blue]\n")
    
    if result["invariants"]["ok"] and result2["invariants"]["ok"]:
        console.print("[green bold]✓ All invariants passed[/green bold]")
    else:
        console.print("[red bold]✗ Invariant violations found[/red bold]")
    
    # Save as SVG then convert to PNG
    svg_path = "docs/demo.svg"
    png_path = "docs/demo.png"
    
    console.save_svg(svg_path, title="Agent Ledger Demo")
    console.print(f"\n[dim]Saved SVG to {svg_path}[/dim]")
    
    # Convert to PNG
    try:
        import cairosvg
        cairosvg.svg2png(url=svg_path, write_to=png_path)
        console.print(f"[green]✓ Generated {png_path}[/green]")
    except ImportError:
        console.print("[yellow]⚠ cairosvg not installed, PNG not generated[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ Error generating PNG: {e}[/red]")


if __name__ == "__main__":
    main()
