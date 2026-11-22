"""Tests for synthetic question generation."""

import pytest
from chunk_bench.models import Document
from chunk_bench.synth import generate_questions


def test_generate_questions_deterministic():
    """Test question generation is deterministic."""
    docs = [
        Document(doc_id="doc1", text="Machine learning is a subset of AI. It enables systems to learn from data."),
        Document(doc_id="doc2", text="Python is a programming language. It is widely used for data science."),
    ]
    
    q1 = generate_questions(docs, n=5, seed=42)
    q2 = generate_questions(docs, n=5, seed=42)
    
    assert len(q1) == len(q2)
    for qa, qb in zip(q1, q2):
        assert qa.question == qb.question
        assert qa.gold_doc == qb.gold_doc


def test_generate_questions_valid():
    """Test generated questions are valid."""
    docs = [
        Document(
            doc_id="test.md",
            text="Machine learning is a powerful technique for data analysis. "
                 "Neural networks can process complex patterns in large datasets. "
                 "Deep learning has revolutionized computer vision and natural language processing."
        ),
    ]
    
    questions = generate_questions(docs, n=3, seed=1)
    
    assert len(questions) > 0
    for q in questions:
        assert len(q.question) > 0
        assert len(q.gold_doc) > 0
        assert q.gold_substring is not None


def test_generate_questions_gold_substring_exists():
    """Test gold substring exists in corpus."""
    docs = [
        Document(
            doc_id="doc1",
            text="Python is a programming language. Machine learning uses Python extensively."
        ),
    ]
    
    questions = generate_questions(docs, n=5, seed=1)
    
    for q in questions:
        doc = next(d for d in docs if d.doc_id == q.gold_doc)
        assert q.gold_substring in doc.text


def test_generate_questions_empty_corpus():
    """Test question generation with empty corpus."""
    questions = generate_questions([], n=10, seed=1)
    
    assert len(questions) == 0


def test_generate_questions_limited_by_corpus():
    """Test question count limited by corpus size."""
    docs = [
        Document(doc_id="tiny", text="Short."),
    ]
    
    questions = generate_questions(docs, n=100, seed=1)
    
    assert len(questions) <= 100
