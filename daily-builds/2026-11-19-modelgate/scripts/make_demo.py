#!/usr/bin/env python3
"""Generate demo SVG and PNG for README."""

import subprocess
from pathlib import Path

from rich.console import Console


def main() -> None:
    """Generate demo artifacts."""
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)

    svg_path = docs_dir / "demo.svg"
    png_path = docs_dir / "demo.png"

    # Create console with recording
    console = Console(record=True, width=100)

    # Capture models command
    console.rule("[bold blue]modelgate models[/]")
    console.print()

    result = subprocess.run(
        ["modelgate", "models", "--config", "models.yaml"],
        capture_output=True,
        text=True,
        cwd=project_root,
        timeout=30,
        check=False,
    )

    if result.returncode == 0:
        console.print(result.stdout)
    else:
        console.print(f"[red]Error:[/] {result.stderr}")

    console.print()

    # Capture simulate command
    console.rule("[bold blue]modelgate simulate examples/trace.jsonl[/]")
    console.print()

    result = subprocess.run(
        [
            "modelgate",
            "simulate",
            "examples/trace.jsonl",
            "--policy",
            "cheapest",
            "--policy",
            "balanced",
            "--policy",
            "quality-first",
        ],
        capture_output=True,
        text=True,
        cwd=project_root,
        timeout=30,
        check=False,
    )

    if result.returncode == 0:
        console.print(result.stdout)
    else:
        console.print(f"[red]Error:[/] {result.stderr}")

    # Save SVG
    console.save_svg(str(svg_path), title="Modelgate Demo")
    print(f"✓ Saved {svg_path}")

    # Convert to PNG
    _convert_svg_to_png(svg_path, png_path)


def _convert_svg_to_png(svg_path: Path, png_path: Path) -> None:
    """Convert SVG to PNG with fallback."""
    try:
        import cairosvg  # noqa: PLC0415

        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), scale=2.0)
        print(f"✓ Saved {png_path}")
    except ImportError:
        # Fallback: create a simple text-based PNG with Pillow
        try:
            from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415

            img = Image.new("RGB", (1000, 800), color="white")
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
            except Exception:
                font = ImageFont.load_default()

            draw.text((10, 10), "Modelgate Demo\n\nSee docs/demo.svg for full rendering", fill="black", font=font)

            img.save(png_path)
            print(f"✓ Saved {png_path} (fallback rendering)")
        except ImportError:
            print("⚠ Could not create PNG (install cairosvg or Pillow)")


if __name__ == "__main__":
    main()
