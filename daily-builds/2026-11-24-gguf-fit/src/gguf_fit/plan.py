"""Fit planning and max-context solving."""

from dataclasses import dataclass
from typing import Literal

from .estimate import MemoryEstimate, estimate
from .summary import ModelSummary, summarize
from .types import GGUFFile
from .units import parse_size


@dataclass
class FitPlan:
    """Fit planning result."""
    verdict: Literal['fits-gpu', 'partial-offload', 'cpu-only', 'does-not-fit']
    gpu_layers: int | None
    gpu_bytes: int
    ram_bytes: int
    estimate: MemoryEstimate


def plan_fit(
    gguf: GGUFFile | ModelSummary,
    vram: str | int,
    ram: str | int = 0,
    ctx: int = 2048,
    kv: str = 'f16',
    parallel: int = 1,
) -> FitPlan:
    """Plan GPU/CPU offload to fit memory budget.
    
    Args:
        gguf: GGUF file or summary
        vram: VRAM budget (string like '24GiB' or bytes)
        ram: RAM budget (string like '32GiB' or bytes)
        ctx: Context length
        kv: KV cache dtype
        parallel: Number of parallel slots
        
    Returns:
        Fit plan with verdict and layer split
    """
    vram_bytes = parse_size(vram) if isinstance(vram, str) else vram
    ram_bytes = parse_size(ram) if isinstance(ram, str) else ram
    
    if isinstance(gguf, GGUFFile):
        summary = summarize(gguf)
    else:
        summary = gguf
    
    # Get full estimate
    est = estimate(gguf, ctx=ctx, kv=kv, parallel=parallel)
    
    # Check if fits entirely in VRAM
    if est.total_bytes <= vram_bytes:
        return FitPlan(
            verdict='fits-gpu',
            gpu_layers=summary.n_layers,
            gpu_bytes=est.total_bytes,
            ram_bytes=0,
            estimate=est,
        )
    
    # Check if doesn't fit anywhere
    if est.total_bytes > vram_bytes + ram_bytes:
        return FitPlan(
            verdict='does-not-fit',
            gpu_layers=0,
            gpu_bytes=0,
            ram_bytes=0,
            estimate=est,
        )
    
    # Try partial offload
    n_layers = summary.n_layers or 0
    if n_layers == 0 or vram_bytes == 0:
        # No GPU, use CPU only
        if est.total_bytes <= ram_bytes:
            return FitPlan(
                verdict='cpu-only',
                gpu_layers=0,
                gpu_bytes=0,
                ram_bytes=est.total_bytes,
                estimate=est,
            )
        else:
            return FitPlan(
                verdict='does-not-fit',
                gpu_layers=0,
                gpu_bytes=0,
                ram_bytes=0,
                estimate=est,
            )
    
    # Find how many layers fit on GPU
    # Heuristic: divide weights roughly evenly per layer, plus embedding/output
    weights_bytes = est.weights_bytes
    kv_cache_bytes = est.kv_cache_bytes
    overhead_bytes = est.overhead_bytes
    
    # Estimate per-layer weight size (rough approximation)
    per_layer_bytes = weights_bytes // (n_layers + 2)  # +2 for embedding/output
    embedding_output_bytes = per_layer_bytes * 2
    
    # Available GPU budget after KV cache and overhead
    gpu_available = vram_bytes - kv_cache_bytes - overhead_bytes
    
    if gpu_available < embedding_output_bytes:
        # Can't even fit embedding, go CPU-only
        if est.total_bytes <= ram_bytes:
            return FitPlan(
                verdict='cpu-only',
                gpu_layers=0,
                gpu_bytes=0,
                ram_bytes=est.total_bytes,
                estimate=est,
            )
        else:
            return FitPlan(
                verdict='does-not-fit',
                gpu_layers=0,
                gpu_bytes=0,
                ram_bytes=0,
                estimate=est,
            )
    
    gpu_available -= embedding_output_bytes
    gpu_layers = min(n_layers, int(gpu_available // per_layer_bytes))
    
    gpu_bytes = embedding_output_bytes + (gpu_layers * per_layer_bytes) + kv_cache_bytes + overhead_bytes
    ram_bytes_used = est.total_bytes - gpu_bytes
    
    if ram_bytes_used <= ram_bytes:
        return FitPlan(
            verdict='partial-offload',
            gpu_layers=gpu_layers,
            gpu_bytes=gpu_bytes,
            ram_bytes=ram_bytes_used,
            estimate=est,
        )
    else:
        return FitPlan(
            verdict='does-not-fit',
            gpu_layers=0,
            gpu_bytes=0,
            ram_bytes=0,
            estimate=est,
        )


def max_context(
    gguf: GGUFFile | ModelSummary,
    vram: str | int,
    ram: str | int = 0,
    kv: str = 'f16',
    parallel: int = 1,
    min_ctx: int = 128,
    max_ctx: int = 1_000_000,
) -> int:
    """Find maximum context length that fits budget (binary search).
    
    Args:
        gguf: GGUF file or summary
        vram: VRAM budget
        ram: RAM budget
        kv: KV cache dtype
        parallel: Number of parallel slots
        min_ctx: Minimum context to try
        max_ctx: Maximum context to try
        
    Returns:
        Maximum context length that fits
    """
    vram_bytes = parse_size(vram) if isinstance(vram, str) else vram
    ram_bytes = parse_size(ram) if isinstance(ram, str) else ram
    
    def fits(ctx: int) -> bool:
        """Check if context length fits."""
        plan = plan_fit(gguf, vram=vram_bytes, ram=ram_bytes, ctx=ctx, kv=kv, parallel=parallel)
        return plan.verdict in ('fits-gpu', 'partial-offload', 'cpu-only')
    
    # Binary search
    left, right = min_ctx, max_ctx
    result = 0
    
    while left <= right:
        mid = (left + right) // 2
        if fits(mid):
            result = mid
            left = mid + 1
        else:
            right = mid - 1
    
    return result
