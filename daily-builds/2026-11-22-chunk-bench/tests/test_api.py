"""Tests for API."""

import pytest
from fastapi.testclient import TestClient
from chunk_bench.api import app

client = TestClient(app)


def test_api_root():
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_api_strategies():
    """Test strategies endpoint."""
    response = client.get("/strategies")
    
    assert response.status_code == 200
    strategies = response.json()
    
    assert len(strategies) > 0
    assert any(s["name"] == "fixed" for s in strategies)
    assert any(s["name"] == "markdown" for s in strategies)


def test_api_evaluate():
    """Test evaluate endpoint."""
    request_data = {
        "texts": [
            {"doc_id": "doc1", "text": "Machine learning is a subset of AI."},
            {"doc_id": "doc2", "text": "Python is a programming language."},
        ],
        "questions": [
            {"question": "What is machine learning?", "gold_doc": "doc1", "gold_substring": "Machine learning"},
        ],
        "config": {
            "strategy": "fixed",
            "size": 10,
            "overlap": 0,
            "retriever": "bm25",
            "k": 3,
            "seed": 1,
        }
    }
    
    response = client.post("/evaluate", json=request_data)
    
    assert response.status_code == 200
    result = response.json()
    
    assert "config" in result
    assert "metrics" in result
    assert "hit_at_k" in result["metrics"]


def test_api_evaluate_invalid():
    """Test evaluate with invalid input."""
    response = client.post("/evaluate", json={})
    
    assert response.status_code == 422
