"""Compare benchmark results against a baseline."""

import json
from pathlib import Path
from .models import BenchmarkResult


def load_baseline(baseline_path: str) -> dict:
    """Load baseline results from JSON."""
    with open(baseline_path, 'r') as f:
        return json.load(f)


def compare_to_baseline(
    current: BenchmarkResult,
    baseline: dict,
    tolerance: float = 0.05
) -> tuple[bool, str]:
    """Compare current result to baseline."""
    baseline_metrics = baseline.get("metrics", {})
    current_metrics = current.metrics.model_dump()
    
    regressions = []
    
    for metric in ["hit_at_k", "mrr", "recall_at_k", "context_precision"]:
        baseline_value = baseline_metrics.get(metric, 0)
        current_value = current_metrics.get(metric, 0)
        
        if current_value < baseline_value - tolerance:
            diff = baseline_value - current_value
            regressions.append(f"{metric}: {current_value:.3f} vs {baseline_value:.3f} (Δ={-diff:.3f})")
    
    if regressions:
        message = "Regressions detected:\n" + "\n".join(regressions)
        return False, message
    
    return True, "No regressions detected"


def save_baseline(result: BenchmarkResult, output_path: str) -> None:
    """Save a result as a baseline."""
    data = {
        "config": result.config.model_dump(),
        "metrics": result.metrics.model_dump(),
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
