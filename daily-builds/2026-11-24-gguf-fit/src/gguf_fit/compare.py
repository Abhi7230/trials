"""Compare two GGUF models."""

from dataclasses import dataclass
from pathlib import Path

from .estimate import estimate
from .reader import read_gguf
from .summary import summarize


@dataclass
class ComparisonRow:
    """Single model comparison data."""
    name: str
    file_size: int
    total_params: int
    effective_bpw: float
    memory_at_ctx: int
    type_histogram: dict[str, int]


@dataclass
class Comparison:
    """Comparison between two models."""
    model_a: ComparisonRow
    model_b: ComparisonRow
    context_length: int
    kv_dtype: str


def compare(path_a: str | Path, path_b: str | Path, ctx: int = 8192, kv: str = 'f16') -> Comparison:
    """Compare two GGUF models.
    
    Args:
        path_a: First model path
        path_b: Second model path
        ctx: Context length for memory comparison
        kv: KV cache dtype
        
    Returns:
        Comparison data
    """
    gguf_a = read_gguf(path_a)
    gguf_b = read_gguf(path_b)
    
    summary_a = summarize(gguf_a)
    summary_b = summarize(gguf_b)
    
    est_a = estimate(summary_a, ctx=ctx, kv=kv)
    est_b = estimate(summary_b, ctx=ctx, kv=kv)
    
    return Comparison(
        model_a=ComparisonRow(
            name=str(Path(path_a).name),
            file_size=summary_a.file_size,
            total_params=summary_a.total_params,
            effective_bpw=summary_a.effective_bpw,
            memory_at_ctx=est_a.total_bytes,
            type_histogram=summary_a.type_histogram,
        ),
        model_b=ComparisonRow(
            name=str(Path(path_b).name),
            file_size=summary_b.file_size,
            total_params=summary_b.total_params,
            effective_bpw=summary_b.effective_bpw,
            memory_at_ctx=est_b.total_bytes,
            type_histogram=summary_b.type_histogram,
        ),
        context_length=ctx,
        kv_dtype=kv,
    )
