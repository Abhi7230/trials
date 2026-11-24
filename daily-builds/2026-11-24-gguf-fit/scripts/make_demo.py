#!/usr/bin/env python3
"""Generate demo.png from rich Console output."""

import sys
import tempfile
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.syntax import Syntax
    import cairosvg
except ImportError:
    print("Error: missing dependencies. Install with: pip install rich cairosvg")
    sys.exit(1)

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from gguf_fit.writer import write_gguf
from gguf_fit.reader import read_gguf
from gguf_fit.summary import summarize
from gguf_fit.plan import plan_fit
from gguf_fit.types import GGMLType
from gguf_fit.units import format_size


def main():
    # Create demo fixture
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        model_path = tmpdir / "demo-llama-7b.gguf"
        
        metadata = {
            "general.architecture": "llama",
            "general.name": "Demo-Llama-7B-Q4_0",
            "llama.block_count": 32,
            "llama.embedding_length": 4096,
            "llama.attention.head_count": 32,
            "llama.attention.head_count_kv": 8,
            "llama.context_length": 32768,
            "llama.vocab_size": 32000,
        }
        
        # Create realistic 7B-ish parameter count with Q4_0
        # 7B params ≈ 3.8 GB in Q4_0
        tensors = [
            ("token_embd.weight", [32000, 4096], GGMLType.Q4_0),
            *[(f"blk.{i}.attn_q.weight", [4096, 4096], GGMLType.Q4_0) for i in range(32)],
            *[(f"blk.{i}.attn_k.weight", [4096, 1024], GGMLType.Q4_0) for i in range(32)],
            *[(f"blk.{i}.attn_v.weight", [4096, 1024], GGMLType.Q4_0) for i in range(32)],
            *[(f"blk.{i}.attn_output.weight", [4096, 4096], GGMLType.Q4_0) for i in range(32)],
            *[(f"blk.{i}.ffn_gate.weight", [4096, 11008], GGMLType.Q4_0) for i in range(32)],
            *[(f"blk.{i}.ffn_up.weight", [4096, 11008], GGMLType.Q4_0) for i in range(32)],
            *[(f"blk.{i}.ffn_down.weight", [11008, 4096], GGMLType.Q4_0) for i in range(32)],
            ("output.weight", [4096, 32000], GGMLType.Q4_0),
        ]
        
        write_gguf(model_path, version=3, metadata=metadata, tensors=tensors)
        gguf = read_gguf(model_path)
        summary = summarize(gguf)
        
        # Create rich output
        console = Console(record=True, width=100)
        
        console.print("\n[bold cyan]gguf-fit[/bold cyan] — GGUF Memory Analyzer\n", justify="left")
        
        # Model summary
        console.print("[bold]Model:[/bold] Demo-Llama-7B-Q4_0", style="yellow")
        console.print(f"Parameters: {summary.total_params:,}")
        console.print(f"File Size: {format_size(summary.file_size)}")
        console.print(f"Effective BPW: {summary.effective_bpw:.2f}")
        console.print()
        
        # Memory estimates table
        table = Table(title="Memory Estimates @ 32k Context", show_header=True)
        table.add_column("KV Dtype", style="cyan")
        table.add_column("Weights", justify="right")
        table.add_column("KV Cache", justify="right")
        table.add_column("Overhead", justify="right")
        table.add_column("Total", justify="right", style="bold green")
        
        from gguf_fit.estimate import estimate
        
        for kv in ['f16', 'q8_0', 'q4_0']:
            est = estimate(summary, ctx=32768, kv=kv)
            table.add_row(
                kv,
                format_size(est.weights_bytes),
                format_size(est.kv_cache_bytes),
                format_size(est.overhead_bytes),
                format_size(est.total_bytes),
            )
        
        console.print(table)
        console.print()
        
        # Fit results
        console.print("[bold]Fit Results:[/bold]", style="yellow")
        
        scenarios = [
            ("24 GiB VRAM", "24GiB", "0"),
            ("16 GiB VRAM", "16GiB", "0"),
            ("8 GiB VRAM + 32 GiB RAM", "8GiB", "32GiB"),
        ]
        
        for desc, vram, ram in scenarios:
            plan = plan_fit(summary, vram=vram, ram=ram, ctx=32768, kv='q8_0')
            verdict_style = "green" if plan.verdict == "fits-gpu" else "yellow" if plan.verdict == "partial-offload" else "red"
            console.print(f"  {desc}: [{verdict_style}]{plan.verdict}[/{verdict_style}]", style="dim")
        
        console.print()
        console.print("[dim]Heuristic estimates • Header-only parsing • Offline tool[/dim]")
        
        # Save SVG then convert to PNG
        svg_path = Path(__file__).parent.parent / 'docs' / 'demo.svg'
        png_path = Path(__file__).parent.parent / 'docs' / 'demo.png'
        
        svg_path.parent.mkdir(exist_ok=True)
        
        console.save_svg(str(svg_path), title="gguf-fit demo")
        
        # Convert to PNG
        with open(svg_path, 'r') as f:
            svg_data = f.read()
        
        cairosvg.svg2png(bytestring=svg_data.encode('utf-8'), write_to=str(png_path), scale=2.0)
        
        print(f"Generated: {png_path}")


if __name__ == '__main__':
    main()
