"""Markdown table formatting."""

from ..models import BenchmarkResult


def format_markdown(results: list[BenchmarkResult]) -> str:
    """Format results as a markdown table."""
    lines = [
        "| Strategy | Size | Overlap | Retriever | Hit@k | MRR | Precision | Tokens | Chunks |",
        "|----------|------|---------|-----------|-------|-----|-----------|--------|--------|",
    ]
    
    for result in sorted(results, key=lambda r: r.metrics.hit_at_k, reverse=True):
        line = (
            f"| {result.config.strategy} "
            f"| {result.config.size} "
            f"| {result.config.overlap} "
            f"| {result.config.retriever} "
            f"| {result.metrics.hit_at_k:.3f} "
            f"| {result.metrics.mrr:.3f} "
            f"| {result.metrics.context_precision:.3f} "
            f"| {result.metrics.avg_tokens_retrieved:.1f} "
            f"| {result.metrics.chunk_count} |"
        )
        lines.append(line)
    
    return "\n".join(lines)
