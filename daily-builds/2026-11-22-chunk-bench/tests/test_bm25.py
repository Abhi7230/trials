"""Tests for BM25 retriever."""

import pytest
from chunk_bench.models import Chunk
from chunk_bench.retrieve.bm25 import BM25Retriever


def test_bm25_basic():
    """Test BM25 basic retrieval."""
    chunks = [
        Chunk(doc_id="1", text="python programming language", start_offset=0, end_offset=27),
        Chunk(doc_id="2", text="java programming tutorial", start_offset=0, end_offset=25),
        Chunk(doc_id="3", text="cooking recipes pasta", start_offset=0, end_offset=21),
    ]
    
    retriever = BM25Retriever()
    retriever.index(chunks)
    
    result = retriever.retrieve("python programming", k=2)
    
    assert len(result.chunks) <= 2
    assert result.chunks[0].doc_id == "1"


def test_bm25_exact_match():
    """Test BM25 with exact term match."""
    chunks = [
        Chunk(doc_id="1", text="machine learning", start_offset=0, end_offset=16),
        Chunk(doc_id="2", text="deep learning neural", start_offset=0, end_offset=20),
        Chunk(doc_id="3", text="supervised learning", start_offset=0, end_offset=19),
    ]
    
    retriever = BM25Retriever()
    retriever.index(chunks)
    
    result = retriever.retrieve("machine", k=1)
    
    assert len(result.chunks) == 1
    assert result.chunks[0].doc_id == "1"


def test_bm25_scores_ordered():
    """Test BM25 scores are in descending order."""
    chunks = [
        Chunk(doc_id=str(i), text=f"document {i} with some text", start_offset=0, end_offset=20)
        for i in range(5)
    ]
    
    retriever = BM25Retriever()
    retriever.index(chunks)
    
    result = retriever.retrieve("document text", k=5)
    
    for i in range(len(result.scores) - 1):
        assert result.scores[i] >= result.scores[i + 1]


def test_bm25_empty_query():
    """Test BM25 with empty query."""
    chunks = [
        Chunk(doc_id="1", text="some content", start_offset=0, end_offset=12),
    ]
    
    retriever = BM25Retriever()
    retriever.index(chunks)
    
    result = retriever.retrieve("", k=1)
    
    assert len(result.chunks) <= 1


def test_bm25_no_chunks():
    """Test BM25 with no indexed chunks."""
    retriever = BM25Retriever()
    result = retriever.retrieve("query", k=3)
    
    assert len(result.chunks) == 0
    assert len(result.scores) == 0
