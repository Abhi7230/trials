"""Retrieval implementations."""

from .dense import DenseRetriever
from .bm25 import BM25Retriever
from .hybrid import HybridRetriever

__all__ = ["DenseRetriever", "BM25Retriever", "HybridRetriever"]


def get_retriever(retriever_type: str, embedder=None):
    """Get a retriever by type."""
    if retriever_type == "dense":
        if embedder is None:
            from ..embed import HashEmbedder
            embedder = HashEmbedder()
        return DenseRetriever(embedder)
    elif retriever_type == "bm25":
        return BM25Retriever()
    elif retriever_type == "hybrid":
        if embedder is None:
            from ..embed import HashEmbedder
            embedder = HashEmbedder()
        return HybridRetriever(embedder)
    else:
        raise ValueError(f"Unknown retriever type: {retriever_type}")
