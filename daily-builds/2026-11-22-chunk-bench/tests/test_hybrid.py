"""Tests for hybrid retriever."""

import pytest
from chunk_bench.models import Chunk
from chunk_bench.embed import HashEmbedder
from chunk_bench.retrieve.hybrid import HybridRetriever


def test_hybrid_retriever_basic():
    """Test hybrid retriever combines dense and BM25."""
    chunks = [
        Chunk(doc_id="1", text="machine learning algorithms", start_offset=0, end_offset=27),
        Chunk(doc_id="2", text="deep learning neural networks", start_offset=0, end_offset=29),
        Chunk(doc_id="3", text="cooking recipes food", start_offset=0, end_offset=20),
    ]
    
    embedder = HashEmbedder(dim=64, seed=1)
    retriever = HybridRetriever(embedder)
    retriever.index(chunks)
    
    result = retriever.retrieve("machine learning", k=2)
    
    assert len(result.chunks) <= 2
    assert result.chunks[0].doc_id in ["1", "2"]


def test_hybrid_retriever_rrf():
    """Test reciprocal rank fusion scoring."""
    chunks = [
        Chunk(doc_id=str(i), text=f"document {i} content", start_offset=0, end_offset=18)
        for i in range(5)
    ]
    
    embedder = HashEmbedder(dim=64, seed=1)
    retriever = HybridRetriever(embedder, k_constant=60)
    retriever.index(chunks)
    
    result = retriever.retrieve("document content", k=3)
    
    assert len(result.chunks) <= 3
    for i in range(len(result.scores) - 1):
        assert result.scores[i] >= result.scores[i + 1]


def test_hybrid_retriever_empty():
    """Test hybrid retriever with no chunks."""
    embedder = HashEmbedder(dim=64, seed=1)
    retriever = HybridRetriever(embedder)
    
    result = retriever.retrieve("query", k=3)
    
    assert len(result.chunks) == 0
    assert len(result.scores) == 0
