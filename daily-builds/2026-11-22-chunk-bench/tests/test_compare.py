"""Tests for baseline comparison."""

import pytest
import tempfile
import json
from pathlib import Path
from chunk_bench.compare import compare_to_baseline, save_baseline, load_baseline
from chunk_bench.models import BenchmarkConfig, BenchmarkResult, MetricResults


def test_compare_to_baseline_pass():
    """Test comparison passes with no regression."""
    current = BenchmarkResult(
        config=BenchmarkConfig(strategy="markdown", size=128, overlap=0, retriever="bm25", k=3, seed=1),
        metrics=MetricResults(
            hit_at_k=0.9, mrr=0.85, recall_at_k=0.9, context_precision=0.5,
            avg_tokens_retrieved=150, chunk_count=40, index_size_bytes=6000, redundancy=0.05
        )
    )
    
    baseline = {
        "metrics": {
            "hit_at_k": 0.85,
            "mrr": 0.80,
            "recall_at_k": 0.85,
            "context_precision": 0.45,
        }
    }
    
    passed, message = compare_to_baseline(current, baseline, tolerance=0.05)
    
    assert passed is True


def test_compare_to_baseline_fail():
    """Test comparison fails with regression."""
    current = BenchmarkResult(
        config=BenchmarkConfig(strategy="markdown", size=128, overlap=0, retriever="bm25", k=3, seed=1),
        metrics=MetricResults(
            hit_at_k=0.7, mrr=0.65, recall_at_k=0.7, context_precision=0.4,
            avg_tokens_retrieved=150, chunk_count=40, index_size_bytes=6000, redundancy=0.05
        )
    )
    
    baseline = {
        "metrics": {
            "hit_at_k": 0.85,
            "mrr": 0.80,
            "recall_at_k": 0.85,
            "context_precision": 0.45,
        }
    }
    
    passed, message = compare_to_baseline(current, baseline, tolerance=0.05)
    
    assert passed is False
    assert "Regressions detected" in message


def test_save_and_load_baseline():
    """Test saving and loading baseline."""
    result = BenchmarkResult(
        config=BenchmarkConfig(strategy="markdown", size=128, overlap=0, retriever="bm25", k=3, seed=1),
        metrics=MetricResults(
            hit_at_k=0.9, mrr=0.85, recall_at_k=0.9, context_precision=0.5,
            avg_tokens_retrieved=150, chunk_count=40, index_size_bytes=6000, redundancy=0.05
        )
    )
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        save_baseline(result, temp_path)
        loaded = load_baseline(temp_path)
        
        assert loaded["config"]["strategy"] == "markdown"
        assert loaded["metrics"]["hit_at_k"] == 0.9
    finally:
        Path(temp_path).unlink()
