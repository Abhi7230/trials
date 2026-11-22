"""Hash-based embedder for deterministic offline testing."""

import hashlib
import numpy as np


class HashEmbedder:
    """Deterministic hash-based embedder using hashing trick."""
    
    def __init__(self, dim: int = 128, seed: int = 1):
        self.dim = dim
        self.seed = seed
        self.rng = np.random.RandomState(seed)
    
    def embed(self, text: str) -> np.ndarray:
        """Embed text to a vector using hashing trick."""
        vec = np.zeros(self.dim)
        tokens = text.lower().split()
        
        for token in tokens:
            hash_val = int(hashlib.md5(
                (token + str(self.seed)).encode()
            ).hexdigest(), 16)
            
            idx = hash_val % self.dim
            sign = 1 if (hash_val // self.dim) % 2 == 0 else -1
            vec[idx] += sign
        
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        
        return vec
    
    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts."""
        return np.array([self.embed(text) for text in texts])
