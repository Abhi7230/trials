"""Tests for dense retriever."""

import pytest
from chunk_bench.models import Chunk
from chunk_bench.embed import HashEmbedder
from chunk_bench.retrieve.dense import DenseRetriever


def test_dense_retriever_basic():
    """Test dense retriever basic functionality."""
    chunks = [
        Chunk(doc_id="1", text="python programming", start_offset=0, end_offset=18),
        Chunk(doc_id="2", text="java development", start_offset=0, end_offset=16),
        Chunk(doc_id="3", text="cooking recipes", start_offset=0, end_offset=15),
    ]
    
    embedder = HashEmbedder(dim=64, seed=1)
    retriever = DenseRetriever(embedder)
    retriever.index(chunks)
    
    result = retriever.retrieve("python code", k=2)
    
    assert len(result.chunks) <= 2
    assert len(result.scores) <= 2


def test_dense_retriever_similarity():
    """Test dense retriever ranks by similarity."""
    chunks = [
        Chunk(doc_id="1", text="machine learning algorithms", start_offset=0, end_offset=27),
        Chunk(doc_id="2", text="cooking pasta recipes", start_offset=0, end_offset=21),
    ]
    
    embedder = HashEmbedder(dim=64, seed=1)
    retriever = DenseRetriever(embedder)
    retriever.index(chunks)
    
    result = retriever.retrieve("machine learning", k=2)
    
    assert result.chunks[0].doc_id == "1"


def test_dense_retriever_empty():
    """Test dense retriever with no chunks."""
    embedder = HashEmbedder(dim=64, seed=1)
    retriever = DenseRetriever(embedder)
    
    result = retriever.retrieve("query", k=3)
    
    assert len(result.chunks) == 0
    assert len(result.scores) == 0


def test_dense_retriever_scores_range():
    """Test dense retriever scores are cosine similarities."""
    chunks = [
        Chunk(doc_id=str(i), text=f"document {i}", start_offset=0, end_offset=11)
        for i in range(3)
    ]
    
    embedder = HashEmbedder(dim=64, seed=1)
    retriever = DenseRetriever(embedder)
    retriever.index(chunks)
    
    result = retriever.retrieve("document", k=3)
    
    for score in result.scores:
        assert -1.0 <= score <= 1.0
