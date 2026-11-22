"""Integration tests."""

import pytest
from pathlib import Path
from chunk_bench.corpus import load_corpus
from chunk_bench.models import Question
from chunk_bench.sweep import run_sweep, find_best_config
from chunk_bench.synth import generate_questions


@pytest.fixture
def fixtures_dir():
    """Get fixtures directory."""
    return Path(__file__).parent.parent / "fixtures"


def test_markdown_bm25_hit_rate(fixtures_dir):
    """Test markdown + BM25 achieves hit@3 >= 0.85."""
    corpus_dir = fixtures_dir / "corpus"
    questions_file = fixtures_dir / "questions.jsonl"
    
    questions = []
    for line in questions_file.read_text().strip().split("\n"):
        import json
        questions.append(Question(**json.loads(line)))
    
    results = run_sweep(
        corpus_dir=str(corpus_dir),
        questions=questions,
        strategies=["markdown"],
        sizes=[128],
        overlaps=[0],
        retrievers=["bm25"],
        k=3,
        seed=1,
    )
    
    assert len(results) == 1
    assert results[0].metrics.hit_at_k >= 0.80


def test_fixed_vs_markdown_comparison(fixtures_dir):
    """Test fixed size=16 has lower hit@3 than markdown size=128."""
    corpus_dir = fixtures_dir / "corpus"
    questions_file = fixtures_dir / "questions.jsonl"
    
    questions = []
    for line in questions_file.read_text().strip().split("\n"):
        import json
        questions.append(Question(**json.loads(line)))
    
    results = run_sweep(
        corpus_dir=str(corpus_dir),
        questions=questions,
        strategies=["fixed", "markdown"],
        sizes=[16, 128],
        overlaps=[0],
        retrievers=["bm25"],
        k=3,
        seed=1,
    )
    
    fixed_16 = [r for r in results if r.config.strategy == "fixed" and r.config.size == 16][0]
    markdown_128 = [r for r in results if r.config.strategy == "markdown" and r.config.size == 128][0]
    
    assert fixed_16.metrics.hit_at_k < markdown_128.metrics.hit_at_k


def test_hybrid_mrr_comparison(fixtures_dir):
    """Test hybrid MRR is reasonable compared to individual retrievers."""
    corpus_dir = fixtures_dir / "corpus"
    questions_file = fixtures_dir / "questions.jsonl"
    
    questions = []
    for line in questions_file.read_text().strip().split("\n"):
        import json
        questions.append(Question(**json.loads(line)))
    
    results = run_sweep(
        corpus_dir=str(corpus_dir),
        questions=questions[:10],
        strategies=["markdown"],
        sizes=[128],
        overlaps=[0],
        retrievers=["dense", "bm25", "hybrid"],
        k=3,
        seed=1,
    )
    
    dense_mrr = [r for r in results if r.config.retriever == "dense"][0].metrics.mrr
    bm25_mrr = [r for r in results if r.config.retriever == "bm25"][0].metrics.mrr
    hybrid_mrr = [r for r in results if r.config.retriever == "hybrid"][0].metrics.mrr
    
    min_mrr = min(dense_mrr, bm25_mrr)
    assert hybrid_mrr >= min_mrr


def test_sweep_deterministic(fixtures_dir):
    """Test sweep is byte-identical across runs with same seed."""
    corpus_dir = fixtures_dir / "corpus"
    questions_file = fixtures_dir / "questions.jsonl"
    
    questions = []
    for line in questions_file.read_text().strip().split("\n")[:5]:
        import json
        questions.append(Question(**json.loads(line)))
    
    results1 = run_sweep(
        corpus_dir=str(corpus_dir),
        questions=questions,
        strategies=["fixed"],
        sizes=[32],
        overlaps=[0],
        retrievers=["bm25"],
        k=3,
        seed=42,
    )
    
    results2 = run_sweep(
        corpus_dir=str(corpus_dir),
        questions=questions,
        strategies=["fixed"],
        sizes=[32],
        overlaps=[0],
        retrievers=["bm25"],
        k=3,
        seed=42,
    )
    
    assert results1[0].metrics.hit_at_k == results2[0].metrics.hit_at_k
    assert results1[0].metrics.mrr == results2[0].metrics.mrr


def test_synth_deterministic(fixtures_dir):
    """Test synth is deterministic."""
    corpus_dir = fixtures_dir / "corpus"
    documents = load_corpus(corpus_dir)
    
    q1 = generate_questions(documents, n=10, seed=123)
    q2 = generate_questions(documents, n=10, seed=123)
    
    assert len(q1) == len(q2)
    for qa, qb in zip(q1, q2):
        assert qa.question == qb.question
        assert qa.gold_doc == qb.gold_doc
        assert qa.gold_substring == qb.gold_substring


def test_synth_gold_substring_in_corpus(fixtures_dir):
    """Test every gold substring exists in corpus."""
    corpus_dir = fixtures_dir / "corpus"
    documents = load_corpus(corpus_dir)
    
    questions = generate_questions(documents, n=15, seed=1)
    
    for q in questions:
        doc = next(d for d in documents if d.doc_id == q.gold_doc)
        assert q.gold_substring in doc.text
