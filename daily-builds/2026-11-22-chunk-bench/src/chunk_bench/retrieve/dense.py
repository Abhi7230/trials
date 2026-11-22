"""Dense retriever using cosine similarity."""

import numpy as np
from ..models import Chunk, RetrievalResult


class DenseRetriever:
    """Dense retrieval using embeddings and cosine similarity."""
    
    def __init__(self, embedder):
        self.embedder = embedder
        self.chunks = []
        self.embeddings = None
    
    def index(self, chunks: list[Chunk]) -> None:
        """Index chunks by computing embeddings."""
        self.chunks = chunks
        texts = [chunk.text for chunk in chunks]
        self.embeddings = self.embedder.embed_batch(texts)
    
    def retrieve(self, query: str, k: int) -> RetrievalResult:
        """Retrieve top-k chunks by cosine similarity."""
        if not self.chunks:
            return RetrievalResult(chunks=[], scores=[])
        
        query_embedding = self.embedder.embed(query)
        scores = np.dot(self.embeddings, query_embedding)
        
        top_k = min(k, len(self.chunks))
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        top_chunks = [self.chunks[i] for i in top_indices]
        top_scores = [float(scores[i]) for i in top_indices]
        
        return RetrievalResult(chunks=top_chunks, scores=top_scores)
