"""Markdown report formatting."""

from ..compare import Comparison
from ..estimate import MemoryEstimate
from ..plan import FitPlan
from ..summary import ModelSummary
from ..units import format_size


def format_summary(summary: ModelSummary, show_tensors: bool = False) -> str:
    """Format model summary as Markdown."""
    lines = ["# Model Summary", ""]
    
    if summary.architecture or summary.name:
        lines.append("## Basic Info")
        lines.append("")
        if summary.architecture:
            lines.append(f"- **Architecture**: {summary.architecture}")
        if summary.name:
            lines.append(f"- **Name**: {summary.name}")
        lines.append("")
    
    lines.append("## Parameters")
    lines.append("")
    lines.append(f"- **Total Parameters**: {summary.total_params:,}")
    lines.append(f"- **File Size**: {format_size(summary.file_size)}")
    lines.append(f"- **Total Tensor Bytes**: {format_size(summary.total_tensor_bytes)}")
    lines.append(f"- **Effective BPW**: {summary.effective_bpw:.2f}")
    lines.append("")
    
    if any([summary.n_layers, summary.embedding_length, summary.n_heads, summary.context_length]):
        lines.append("## Architecture Details")
        lines.append("")
        if summary.n_layers is not None:
            lines.append(f"- **Layers**: {summary.n_layers}")
        if summary.embedding_length is not None:
            lines.append(f"- **Embedding Length**: {summary.embedding_length}")
        if summary.n_heads is not None:
            lines.append(f"- **Attention Heads**: {summary.n_heads}")
        if summary.n_kv_heads is not None:
            lines.append(f"- **KV Heads**: {summary.n_kv_heads}")
        if summary.context_length is not None:
            lines.append(f"- **Context Length**: {summary.context_length}")
        if summary.expert_count is not None:
            lines.append(f"- **Expert Count**: {summary.expert_count}")
        if summary.vocab_size is not None:
            lines.append(f"- **Vocab Size**: {summary.vocab_size}")
        if summary.sliding_window is not None:
            lines.append(f"- **Sliding Window**: {summary.sliding_window}")
        lines.append("")
    
    lines.append("## Type Histogram")
    lines.append("")
    for type_name, count in sorted(summary.type_histogram.items()):
        lines.append(f"- **{type_name}**: {count}")
    lines.append("")
    
    if show_tensors and summary.largest_tensors:
        lines.append("## Largest Tensors")
        lines.append("")
        for name, size, type_name in summary.largest_tensors:
            lines.append(f"- **{name}**: {format_size(size)} ({type_name})")
        lines.append("")
    
    return "\n".join(lines)


def format_estimate(estimate: MemoryEstimate) -> str:
    """Format memory estimate as Markdown."""
    lines = ["# Memory Estimate", ""]
    lines.append(f"- **Context Length**: {estimate.context_length}")
    lines.append(f"- **KV Dtype**: {estimate.kv_dtype}")
    lines.append(f"- **Parallel Slots**: {estimate.parallel_slots}")
    lines.append("")
    lines.append(f"- **Weights**: {format_size(estimate.weights_bytes)}")
    lines.append(f"- **KV Cache**: {format_size(estimate.kv_cache_bytes)}")
    lines.append(f"- **Overhead**: {format_size(estimate.overhead_bytes)}")
    lines.append(f"- **Total**: {format_size(estimate.total_bytes)}")
    lines.append("")
    
    return "\n".join(lines)


def format_plan(plan: FitPlan) -> str:
    """Format fit plan as Markdown."""
    lines = ["# Fit Plan", ""]
    lines.append(f"- **Verdict**: `{plan.verdict}`")
    
    if plan.gpu_layers is not None:
        lines.append(f"- **GPU Layers**: {plan.gpu_layers}")
    
    lines.append(f"- **GPU Memory**: {format_size(plan.gpu_bytes)}")
    lines.append(f"- **RAM Memory**: {format_size(plan.ram_bytes)}")
    lines.append("")
    lines.append(format_estimate(plan.estimate))
    
    return "\n".join(lines)


def format_comparison(comparison: Comparison) -> str:
    """Format comparison as Markdown."""
    lines = ["# Model Comparison", ""]
    lines.append(f"- **Context Length**: {comparison.context_length}")
    lines.append(f"- **KV Dtype**: {comparison.kv_dtype}")
    lines.append("")
    
    a = comparison.model_a
    b = comparison.model_b
    
    lines.append("| Metric | Model A | Model B |")
    lines.append("|--------|---------|---------|")
    lines.append(f"| Name | {a.name} | {b.name} |")
    lines.append(f"| File Size | {format_size(a.file_size)} | {format_size(b.file_size)} |")
    lines.append(f"| Total Params | {a.total_params:,} | {b.total_params:,} |")
    lines.append(f"| Effective BPW | {a.effective_bpw:.2f} | {b.effective_bpw:.2f} |")
    lines.append(f"| Memory @ Context | {format_size(a.memory_at_ctx)} | {format_size(b.memory_at_ctx)} |")
    lines.append("")
    
    all_types = set(a.type_histogram.keys()) | set(b.type_histogram.keys())
    if any(a.type_histogram.get(t, 0) != b.type_histogram.get(t, 0) for t in all_types):
        lines.append("## Type Differences")
        lines.append("")
        for type_name in sorted(all_types):
            count_a = a.type_histogram.get(type_name, 0)
            count_b = b.type_histogram.get(type_name, 0)
            if count_a != count_b:
                lines.append(f"- **{type_name}**: {count_a} vs {count_b}")
        lines.append("")
    
    return "\n".join(lines)
