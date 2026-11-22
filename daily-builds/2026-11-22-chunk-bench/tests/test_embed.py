"""Tests for embedder."""

import pytest
import numpy as np
from chunk_bench.embed import HashEmbedder


def test_hash_embedder_deterministic():
    """Test embedder is deterministic."""
    embedder = HashEmbedder(dim=128, seed=1)
    text = "hello world"
    
    vec1 = embedder.embed(text)
    vec2 = embedder.embed(text)
    
    np.testing.assert_array_equal(vec1, vec2)


def test_hash_embedder_different_seeds():
    """Test different seeds produce different embeddings."""
    text = "hello world"
    
    vec1 = HashEmbedder(dim=128, seed=1).embed(text)
    vec2 = HashEmbedder(dim=128, seed=2).embed(text)
    
    assert not np.array_equal(vec1, vec2)


def test_hash_embedder_normalized():
    """Test embeddings are L2-normalized."""
    embedder = HashEmbedder(dim=128, seed=1)
    text = "hello world test"
    
    vec = embedder.embed(text)
    norm = np.linalg.norm(vec)
    
    assert abs(norm - 1.0) < 1e-6


def test_hash_embedder_similar_texts():
    """Test similar texts have positive cosine similarity."""
    embedder = HashEmbedder(dim=128, seed=1)
    
    vec1 = embedder.embed("machine learning algorithms")
    vec2 = embedder.embed("machine learning models")
    vec3 = embedder.embed("cooking pasta recipes")
    
    sim_12 = np.dot(vec1, vec2)
    sim_13 = np.dot(vec1, vec3)
    
    assert sim_12 > sim_13


def test_hash_embedder_batch():
    """Test batch embedding."""
    embedder = HashEmbedder(dim=128, seed=1)
    texts = ["hello", "world", "test"]
    
    batch_vecs = embedder.embed_batch(texts)
    
    assert batch_vecs.shape == (3, 128)
    
    for i, text in enumerate(texts):
        single_vec = embedder.embed(text)
        np.testing.assert_array_equal(batch_vecs[i], single_vec)


def test_hash_embedder_empty_text():
    """Test embedding empty text."""
    embedder = HashEmbedder(dim=128, seed=1)
    vec = embedder.embed("")
    
    assert vec.shape == (128,)
    assert np.linalg.norm(vec) == 0.0
