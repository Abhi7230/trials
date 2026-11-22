"""JSON output formatting."""

import json
from ..models import BenchmarkResult


def format_json(results: list[BenchmarkResult]) -> str:
    """Format results as JSON."""
    data = [
        {
            "config": result.config.model_dump(),
            "metrics": result.metrics.model_dump(),
        }
        for result in results
    ]
    return json.dumps(data, indent=2)
