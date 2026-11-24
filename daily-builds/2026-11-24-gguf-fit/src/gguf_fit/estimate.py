"""Memory estimation."""

from dataclasses import dataclass

from .summary import ModelSummary, summarize
from .types import GGMLType, GGUFFile


@dataclass
class MemoryEstimate:
    """Memory usage estimate."""
    weights_bytes: int
    kv_cache_bytes: int
    overhead_bytes: int
    total_bytes: int
    context_length: int
    kv_dtype: str
    parallel_slots: int


def estimate(
    gguf: GGUFFile | ModelSummary,
    ctx: int = 2048,
    kv: str = 'f16',
    parallel: int = 1,
    overhead_pct: float = 0.05,
    overhead_base: int = 256 * 1024 * 1024,
) -> MemoryEstimate:
    """Estimate memory usage.
    
    Args:
        gguf: GGUF file or summary
        ctx: Context length
        kv: KV cache dtype (f16, q8_0, q4_0, bf16)
        parallel: Number of parallel slots
        overhead_pct: Overhead as percentage of weights (default 5%)
        overhead_base: Base overhead in bytes (default 256 MiB)
        
    Returns:
        Memory estimate
    """
    if isinstance(gguf, GGUFFile):
        summary = summarize(gguf)
    else:
        summary = gguf
    
    # Weights
    weights_bytes = summary.total_tensor_bytes
    
    # KV cache
    kv_bytes_per_elem = _get_kv_bytes_per_elem(kv)
    
    n_layers = summary.n_layers or 0
    n_kv_heads = summary.n_kv_heads or summary.n_heads or 0
    embedding_length = summary.embedding_length or 0
    
    if n_heads := summary.n_heads:
        head_dim = embedding_length // n_heads if n_heads > 0 else 0
    else:
        head_dim = 0
    
    # Handle sliding window
    sliding_window = summary.sliding_window
    if sliding_window and sliding_window > 0:
        effective_ctx = min(ctx, sliding_window)
    else:
        effective_ctx = ctx
    
    # KV cache formula: 2 * n_layers * n_ctx * n_kv_heads * head_dim * bytes_per_elem
    kv_cache_bytes = 2 * n_layers * effective_ctx * n_kv_heads * head_dim * kv_bytes_per_elem
    kv_cache_bytes *= parallel
    
    # Overhead: heuristic
    overhead_bytes = int(weights_bytes * overhead_pct) + overhead_base
    
    total_bytes = weights_bytes + kv_cache_bytes + overhead_bytes
    
    return MemoryEstimate(
        weights_bytes=weights_bytes,
        kv_cache_bytes=kv_cache_bytes,
        overhead_bytes=overhead_bytes,
        total_bytes=total_bytes,
        context_length=ctx,
        kv_dtype=kv,
        parallel_slots=parallel,
    )


def _get_kv_bytes_per_elem(kv: str) -> float:
    """Get bytes per element for KV cache dtype."""
    kv = kv.lower()
    if kv in ('f16', 'fp16'):
        return 2.0
    elif kv == 'bf16':
        return 2.0
    elif kv == 'q8_0':
        return 34 / 32  # block size 32, bytes per block 34
    elif kv == 'q4_0':
        return 18 / 32  # block size 32, bytes per block 18
    elif kv == 'f32':
        return 4.0
    else:
        return 2.0
