"""Tests for sweep functionality."""

import pytest
from chunk_bench.sweep import find_best_config, find_pareto_frontier
from chunk_bench.models import BenchmarkConfig, BenchmarkResult, MetricResults


def test_find_best_config():
    """Test finding best configuration."""
    results = [
        BenchmarkResult(
            config=BenchmarkConfig(strategy="fixed", size=64, overlap=0, retriever="bm25", k=3, seed=1),
            metrics=MetricResults(
                hit_at_k=0.7, mrr=0.6, recall_at_k=0.7, context_precision=0.4,
                avg_tokens_retrieved=100, chunk_count=50, index_size_bytes=5000, redundancy=0.1
            )
        ),
        BenchmarkResult(
            config=BenchmarkConfig(strategy="markdown", size=128, overlap=0, retriever="bm25", k=3, seed=1),
            metrics=MetricResults(
                hit_at_k=0.9, mrr=0.85, recall_at_k=0.9, context_precision=0.5,
                avg_tokens_retrieved=150, chunk_count=40, index_size_bytes=6000, redundancy=0.05
            )
        ),
    ]
    
    best = find_best_config(results, metric="hit_at_k")
    
    assert best.metrics.hit_at_k == 0.9
    assert best.config.strategy == "markdown"


def test_find_pareto_frontier():
    """Test Pareto frontier calculation."""
    results = [
        BenchmarkResult(
            config=BenchmarkConfig(strategy="a", size=64, overlap=0, retriever="bm25", k=3, seed=1),
            metrics=MetricResults(
                hit_at_k=0.8, mrr=0.7, recall_at_k=0.8, context_precision=0.4,
                avg_tokens_retrieved=100, chunk_count=50, index_size_bytes=5000, redundancy=0.1
            )
        ),
        BenchmarkResult(
            config=BenchmarkConfig(strategy="b", size=128, overlap=0, retriever="bm25", k=3, seed=1),
            metrics=MetricResults(
                hit_at_k=0.9, mrr=0.85, recall_at_k=0.9, context_precision=0.5,
                avg_tokens_retrieved=200, chunk_count=40, index_size_bytes=6000, redundancy=0.05
            )
        ),
        BenchmarkResult(
            config=BenchmarkConfig(strategy="c", size=256, overlap=0, retriever="bm25", k=3, seed=1),
            metrics=MetricResults(
                hit_at_k=0.7, mrr=0.6, recall_at_k=0.7, context_precision=0.3,
                avg_tokens_retrieved=300, chunk_count=30, index_size_bytes=7000, redundancy=0.02
            )
        ),
    ]
    
    pareto = find_pareto_frontier(results)
    
    assert len(pareto) >= 1
    assert any(r.config.strategy in ["a", "b"] for r in pareto)
