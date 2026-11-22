"""BM25 retriever implementation."""

import math
from collections import Counter, defaultdict
from ..models import Chunk, RetrievalResult
from ..tokenize import tokenize_for_retrieval


class BM25Retriever:
    """BM25 ranking function for text retrieval."""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks = []
        self.doc_freqs = defaultdict(int)
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.doc_term_freqs = []
    
    def index(self, chunks: list[Chunk]) -> None:
        """Index chunks for BM25 retrieval."""
        self.chunks = chunks
        self.doc_term_freqs = []
        self.doc_lengths = []
        self.doc_freqs = defaultdict(int)
        
        for chunk in chunks:
            tokens = tokenize_for_retrieval(chunk.text)
            self.doc_lengths.append(len(tokens))
            term_freqs = Counter(tokens)
            self.doc_term_freqs.append(term_freqs)
            
            for term in term_freqs.keys():
                self.doc_freqs[term] += 1
        
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0
    
    def retrieve(self, query: str, k: int) -> RetrievalResult:
        """Retrieve top-k chunks using BM25."""
        if not self.chunks:
            return RetrievalResult(chunks=[], scores=[])
        
        query_tokens = tokenize_for_retrieval(query)
        scores = []
        
        for idx, chunk in enumerate(self.chunks):
            score = self._score(query_tokens, idx)
            scores.append(score)
        
        top_k = min(k, len(self.chunks))
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        top_chunks = [self.chunks[i] for i in top_indices]
        top_scores = [scores[i] for i in top_indices]
        
        return RetrievalResult(chunks=top_chunks, scores=top_scores)
    
    def _score(self, query_tokens: list[str], doc_idx: int) -> float:
        """Calculate BM25 score for a document."""
        score = 0.0
        doc_length = self.doc_lengths[doc_idx]
        term_freqs = self.doc_term_freqs[doc_idx]
        n = len(self.chunks)
        
        for term in query_tokens:
            if term not in term_freqs:
                continue
            
            tf = term_freqs[term]
            df = self.doc_freqs[term]
            idf = math.log((n - df + 0.5) / (df + 0.5) + 1.0)
            
            norm_tf = (tf * (self.k1 + 1)) / (
                tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
            )
            
            score += idf * norm_tf
        
        return score
