"""Rich table formatting."""

from rich.console import Console
from rich.table import Table
from ..models import BenchmarkResult


def format_table(results: list[BenchmarkResult], highlight_best: bool = True) -> None:
    """Format results as a rich table."""
    console = Console()
    
    best_hit = max(r.metrics.hit_at_k for r in results) if results else 0
    
    table = Table(title="Chunking Benchmark Results")
    table.add_column("Strategy", style="cyan")
    table.add_column("Size", style="magenta")
    table.add_column("Overlap", style="magenta")
    table.add_column("Retriever", style="green")
    table.add_column("Hit@k", style="yellow")
    table.add_column("MRR", style="yellow")
    table.add_column("Precision", style="yellow")
    table.add_column("Tokens", style="blue")
    table.add_column("Chunks", style="blue")
    
    for result in sorted(results, key=lambda r: r.metrics.hit_at_k, reverse=True):
        style = "bold" if highlight_best and result.metrics.hit_at_k == best_hit else ""
        
        table.add_row(
            result.config.strategy,
            str(result.config.size),
            str(result.config.overlap),
            result.config.retriever,
            f"{result.metrics.hit_at_k:.3f}",
            f"{result.metrics.mrr:.3f}",
            f"{result.metrics.context_precision:.3f}",
            f"{result.metrics.avg_tokens_retrieved:.1f}",
            str(result.metrics.chunk_count),
            style=style,
        )
    
    console.print(table)
