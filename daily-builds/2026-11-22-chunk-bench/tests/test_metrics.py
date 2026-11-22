"""Tests for evaluation metrics."""

import pytest
from chunk_bench.models import Chunk, Question, RetrievalResult
from chunk_bench.metrics import is_relevant, calculate_metrics, calculate_redundancy


def test_is_relevant_substring():
    """Test relevance by substring match."""
    chunk = Chunk(
        doc_id="test.md",
        text="This is about machine learning algorithms",
        start_offset=0,
        end_offset=41
    )
    question = Question(
        question="What is machine learning?",
        gold_doc="test.md",
        gold_substring="machine learning"
    )
    
    assert is_relevant(chunk, question) is True


def test_is_relevant_no_match():
    """Test irrelevant chunk."""
    chunk = Chunk(
        doc_id="test.md",
        text="Cooking pasta recipes",
        start_offset=0,
        end_offset=21
    )
    question = Question(
        question="What is machine learning?",
        gold_doc="test.md",
        gold_substring="machine learning"
    )
    
    assert is_relevant(chunk, question) is False


def test_calculate_metrics_perfect():
    """Test metrics with perfect retrieval."""
    questions = [
        Question(question="Q1", gold_doc="doc1", gold_substring="answer"),
        Question(question="Q2", gold_doc="doc2", gold_substring="result"),
    ]
    
    results = [
        RetrievalResult(
            chunks=[Chunk(doc_id="doc1", text="the answer is here", start_offset=0, end_offset=18)],
            scores=[1.0]
        ),
        RetrievalResult(
            chunks=[Chunk(doc_id="doc2", text="the result shown", start_offset=0, end_offset=16)],
            scores=[1.0]
        ),
    ]
    
    all_chunks = [c for r in results for c in r.chunks]
    metrics = calculate_metrics(questions, results, all_chunks, k=1)
    
    assert metrics.hit_at_k == 1.0
    assert metrics.mrr == 1.0
    assert metrics.recall_at_k == 1.0


def test_calculate_metrics_partial():
    """Test metrics with partial success."""
    questions = [
        Question(question="Q1", gold_doc="doc1", gold_substring="answer"),
        Question(question="Q2", gold_doc="doc2", gold_substring="result"),
    ]
    
    results = [
        RetrievalResult(
            chunks=[Chunk(doc_id="doc1", text="the answer", start_offset=0, end_offset=10)],
            scores=[1.0]
        ),
        RetrievalResult(
            chunks=[Chunk(doc_id="doc3", text="wrong doc", start_offset=0, end_offset=9)],
            scores=[1.0]
        ),
    ]
    
    all_chunks = [c for r in results for c in r.chunks]
    metrics = calculate_metrics(questions, results, all_chunks, k=1)
    
    assert metrics.hit_at_k == 0.5
    assert 0 < metrics.mrr < 1.0


def test_calculate_metrics_mrr():
    """Test MRR calculation."""
    questions = [
        Question(question="Q1", gold_doc="doc1", gold_substring="target"),
    ]
    
    results = [
        RetrievalResult(
            chunks=[
                Chunk(doc_id="doc2", text="wrong", start_offset=0, end_offset=5),
                Chunk(doc_id="doc1", text="the target", start_offset=0, end_offset=10),
            ],
            scores=[1.0, 0.8]
        ),
    ]
    
    all_chunks = [c for r in results for c in r.chunks]
    metrics = calculate_metrics(questions, results, all_chunks, k=3)
    
    assert metrics.mrr == 0.5


def test_calculate_redundancy():
    """Test redundancy calculation."""
    chunks = [
        Chunk(doc_id="doc", text="overlap", start_offset=0, end_offset=10),
        Chunk(doc_id="doc", text="content", start_offset=5, end_offset=15),
    ]
    
    redundancy = calculate_redundancy(chunks)
    
    assert 0 <= redundancy <= 1.0


def test_calculate_redundancy_no_overlap():
    """Test redundancy with no overlap."""
    chunks = [
        Chunk(doc_id="doc", text="first", start_offset=0, end_offset=5),
        Chunk(doc_id="doc", text="second", start_offset=10, end_offset=16),
    ]
    
    redundancy = calculate_redundancy(chunks)
    
    assert redundancy == 0.0


def test_metrics_empty():
    """Test metrics with empty inputs."""
    metrics = calculate_metrics([], [], [], k=3)
    
    assert metrics.hit_at_k == 0.0
    assert metrics.mrr == 0.0
    assert metrics.chunk_count == 0
