"""Generate demo visualization."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from chunk_bench.sweep import run_sweep
from chunk_bench.report.table import format_table
from chunk_bench.models import Question
from rich.console import Console
import json

def main():
    """Generate demo screenshot."""
    fixtures_dir = project_root / "fixtures"
    corpus_dir = fixtures_dir / "corpus"
    questions_file = fixtures_dir / "questions.jsonl"
    
    questions = []
    for line in questions_file.read_text().strip().split("\n"):
        questions.append(Question(**json.loads(line)))
    
    console = Console(record=True, width=120)
    
    console.print("[bold cyan]Chunk Bench Demo - Comparing Chunking Strategies[/bold cyan]\n")
    
    results = run_sweep(
        corpus_dir=str(corpus_dir),
        questions=questions[:15],
        strategies=["fixed", "sentence", "markdown"],
        sizes=[64, 128],
        overlaps=[0],
        retrievers=["bm25"],
        k=3,
        seed=1,
    )
    
    best_hit = max(r.metrics.hit_at_k for r in results)
    
    from rich.table import Table
    table = Table(title="Benchmark Results")
    table.add_column("Strategy", style="cyan")
    table.add_column("Size", style="magenta")
    table.add_column("Retriever", style="green")
    table.add_column("Hit@3", style="yellow")
    table.add_column("MRR", style="yellow")
    table.add_column("Tokens", style="blue")
    table.add_column("Chunks", style="blue")
    
    for result in sorted(results, key=lambda r: r.metrics.hit_at_k, reverse=True):
        style = "bold green" if result.metrics.hit_at_k == best_hit else ""
        
        table.add_row(
            result.config.strategy,
            str(result.config.size),
            result.config.retriever,
            f"{result.metrics.hit_at_k:.3f}",
            f"{result.metrics.mrr:.3f}",
            f"{result.metrics.avg_tokens_retrieved:.1f}",
            str(result.metrics.chunk_count),
            style=style,
        )
    
    console.print(table)
    console.print(f"\n[green]✓[/green] Best config: [bold]{results[0].config.strategy}[/bold] "
                  f"(size={results[0].config.size}) with Hit@3 = {best_hit:.3f}")
    
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    svg_path = docs_dir / "demo.svg"
    console.save_svg(str(svg_path), title="Chunk Bench Demo")
    
    try:
        import cairosvg
        png_path = docs_dir / "demo.png"
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=1200)
        print(f"Demo saved to {png_path}")
        svg_path.unlink()
    except ImportError:
        print(f"Demo saved to {svg_path} (cairosvg not available for PNG conversion)")

if __name__ == "__main__":
    main()
