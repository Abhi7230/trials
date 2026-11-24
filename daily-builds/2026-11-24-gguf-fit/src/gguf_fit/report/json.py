"""JSON report formatting."""

import json
from typing import Any

from ..compare import Comparison
from ..estimate import MemoryEstimate
from ..plan import FitPlan
from ..summary import ModelSummary


def format_summary(summary: ModelSummary, show_tensors: bool = False) -> str:
    """Format model summary as JSON."""
    data: dict[str, Any] = {
        "architecture": summary.architecture,
        "name": summary.name,
        "n_layers": summary.n_layers,
        "embedding_length": summary.embedding_length,
        "n_heads": summary.n_heads,
        "n_kv_heads": summary.n_kv_heads,
        "context_length": summary.context_length,
        "expert_count": summary.expert_count,
        "vocab_size": summary.vocab_size,
        "rope_freq_base": summary.rope_freq_base,
        "rope_freq_scale": summary.rope_freq_scale,
        "sliding_window": summary.sliding_window,
        "total_params": summary.total_params,
        "file_size": summary.file_size,
        "total_tensor_bytes": summary.total_tensor_bytes,
        "effective_bpw": round(summary.effective_bpw, 2),
        "type_histogram": dict(sorted(summary.type_histogram.items())),
    }
    
    if show_tensors:
        data["largest_tensors"] = [
            {"name": name, "size_bytes": size, "type": type_name}
            for name, size, type_name in summary.largest_tensors
        ]
    
    return json.dumps(data, indent=2, sort_keys=True)


def format_estimate(estimate: MemoryEstimate) -> str:
    """Format memory estimate as JSON."""
    data = {
        "context_length": estimate.context_length,
        "kv_dtype": estimate.kv_dtype,
        "kv_cache_bytes": estimate.kv_cache_bytes,
        "overhead_bytes": estimate.overhead_bytes,
        "parallel_slots": estimate.parallel_slots,
        "total_bytes": estimate.total_bytes,
        "weights_bytes": estimate.weights_bytes,
    }
    return json.dumps(data, indent=2, sort_keys=True)


def format_plan(plan: FitPlan) -> str:
    """Format fit plan as JSON."""
    data = {
        "estimate": {
            "context_length": plan.estimate.context_length,
            "kv_cache_bytes": plan.estimate.kv_cache_bytes,
            "kv_dtype": plan.estimate.kv_dtype,
            "overhead_bytes": plan.estimate.overhead_bytes,
            "parallel_slots": plan.estimate.parallel_slots,
            "total_bytes": plan.estimate.total_bytes,
            "weights_bytes": plan.estimate.weights_bytes,
        },
        "gpu_bytes": plan.gpu_bytes,
        "gpu_layers": plan.gpu_layers,
        "ram_bytes": plan.ram_bytes,
        "verdict": plan.verdict,
    }
    return json.dumps(data, indent=2, sort_keys=True)


def format_comparison(comparison: Comparison) -> str:
    """Format comparison as JSON."""
    data = {
        "context_length": comparison.context_length,
        "kv_dtype": comparison.kv_dtype,
        "model_a": {
            "effective_bpw": round(comparison.model_a.effective_bpw, 2),
            "file_size": comparison.model_a.file_size,
            "memory_at_ctx": comparison.model_a.memory_at_ctx,
            "name": comparison.model_a.name,
            "total_params": comparison.model_a.total_params,
            "type_histogram": dict(sorted(comparison.model_a.type_histogram.items())),
        },
        "model_b": {
            "effective_bpw": round(comparison.model_b.effective_bpw, 2),
            "file_size": comparison.model_b.file_size,
            "memory_at_ctx": comparison.model_b.memory_at_ctx,
            "name": comparison.model_b.name,
            "total_params": comparison.model_b.total_params,
            "type_histogram": dict(sorted(comparison.model_b.type_histogram.items())),
        },
    }
    return json.dumps(data, indent=2, sort_keys=True)
