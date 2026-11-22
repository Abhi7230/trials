"""Tests for report formatting."""

import pytest
from chunk_bench.models import BenchmarkConfig, BenchmarkResult, MetricResults
from chunk_bench.report import format_json, format_markdown


def test_format_json():
    """Test JSON formatting."""
    results = [
        BenchmarkResult(
            config=BenchmarkConfig(strategy="fixed", size=64, overlap=0, retriever="bm25", k=3, seed=1),
            metrics=MetricResults(
                hit_at_k=0.8, mrr=0.7, recall_at_k=0.8, context_precision=0.4,
                avg_tokens_retrieved=100, chunk_count=50, index_size_bytes=5000, redundancy=0.1
            )
        ),
    ]
    
    output = format_json(results)
    
    assert '"strategy": "fixed"' in output
    assert '"hit_at_k": 0.8' in output


def test_format_markdown():
    """Test markdown formatting."""
    results = [
        BenchmarkResult(
            config=BenchmarkConfig(strategy="markdown", size=128, overlap=0, retriever="bm25", k=3, seed=1),
            metrics=MetricResults(
                hit_at_k=0.9, mrr=0.85, recall_at_k=0.9, context_precision=0.5,
                avg_tokens_retrieved=150, chunk_count=40, index_size_bytes=6000, redundancy=0.05
            )
        ),
    ]
    
    output = format_markdown(results)
    
    assert "| Strategy |" in output
    assert "markdown" in output
    assert "0.9" in output


def test_format_markdown_sorted():
    """Test markdown output is sorted by hit@k."""
    results = [
        BenchmarkResult(
            config=BenchmarkConfig(strategy="a", size=64, overlap=0, retriever="bm25", k=3, seed=1),
            metrics=MetricResults(
                hit_at_k=0.7, mrr=0.6, recall_at_k=0.7, context_precision=0.4,
                avg_tokens_retrieved=100, chunk_count=50, index_size_bytes=5000, redundancy=0.1
            )
        ),
        BenchmarkResult(
            config=BenchmarkConfig(strategy="b", size=128, overlap=0, retriever="bm25", k=3, seed=1),
            metrics=MetricResults(
                hit_at_k=0.9, mrr=0.85, recall_at_k=0.9, context_precision=0.5,
                avg_tokens_retrieved=150, chunk_count=40, index_size_bytes=6000, redundancy=0.05
            )
        ),
    ]
    
    output = format_markdown(results)
    lines = output.split("\n")
    
    first_data_line = lines[2]
    assert "b" in first_data_line
