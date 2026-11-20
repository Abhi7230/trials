#!/usr/bin/env python3
"""Generate demo SVG and PNG for the README."""

import sys
from pathlib import Path

from rich.console import Console

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentlens.formatters import format_cli
from agentlens.scorer import analyze_trace
from agentlens.trace_loader import load_trace


def main() -> None:
    """Generate demo assets."""
    # Load the bad trace
    examples_dir = Path(__file__).parent.parent / "examples"
    trace_file = examples_dir / "bad-trace.jsonl"

    events = load_trace(trace_file)
    result = analyze_trace(events)

    # Create console with recording
    console = Console(record=True, width=100)

    # Print the formatted output
    console.print()
    console.print("[bold cyan]$ agentlens analyze examples/bad-trace.jsonl[/bold cyan]")
    console.print()

    # Format the result
    output = format_cli(result, verbose=False)
    console.print(output)

    # Save SVG
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    svg_path = docs_dir / "demo.svg"
    console.save_svg(str(svg_path), title="agentlens demo")
    print(f"✓ Generated {svg_path}")

    # Convert to PNG
    try:
        import cairosvg
        from PIL import Image

        png_path = docs_dir / "demo.png"

        # Use cairosvg
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path))
        print(f"✓ Generated {png_path} (cairosvg)")

    except ImportError:
        try:
            # Fallback to PIL with rsvg
            from PIL import Image

            png_path = docs_dir / "demo.png"
            img = Image.open(svg_path)
            img.save(png_path)
            print(f"✓ Generated {png_path} (Pillow fallback)")
        except Exception as e:
            print(f"⚠ Could not generate PNG: {e}")
            print("  Install cairosvg for PNG generation: pip install cairosvg")


if __name__ == "__main__":
    main()
