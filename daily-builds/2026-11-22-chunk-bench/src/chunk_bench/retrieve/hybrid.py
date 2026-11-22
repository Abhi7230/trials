"""Hybrid retriever using dense + BM25 with reciprocal rank fusion."""

from ..models import Chunk, RetrievalResult
from .dense import DenseRetriever
from .bm25 import BM25Retriever


class HybridRetriever:
    """Hybrid retrieval using reciprocal rank fusion."""
    
    def __init__(self, embedder, k_constant: int = 60):
        self.dense = DenseRetriever(embedder)
        self.bm25 = BM25Retriever()
        self.k_constant = k_constant
    
    def index(self, chunks: list[Chunk]) -> None:
        """Index chunks with both retrievers."""
        self.dense.index(chunks)
        self.bm25.index(chunks)
    
    def retrieve(self, query: str, k: int) -> RetrievalResult:
        """Retrieve using reciprocal rank fusion."""
        if not self.dense.chunks:
            return RetrievalResult(chunks=[], scores=[])
        
        dense_result = self.dense.retrieve(query, len(self.dense.chunks))
        bm25_result = self.bm25.retrieve(query, len(self.bm25.chunks))
        
        rrf_scores = {}
        
        for rank, chunk in enumerate(dense_result.chunks):
            chunk_id = id(chunk)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (self.k_constant + rank + 1)
        
        for rank, chunk in enumerate(bm25_result.chunks):
            chunk_id = id(chunk)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (self.k_constant + rank + 1)
        
        all_chunks = {id(c): c for c in self.dense.chunks}
        sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        top_k = min(k, len(sorted_items))
        top_chunks = [all_chunks[chunk_id] for chunk_id, _ in sorted_items[:top_k]]
        top_scores = [score for _, score in sorted_items[:top_k]]
        
        return RetrievalResult(chunks=top_chunks, scores=top_scores)
