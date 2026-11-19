"""Tests for FastAPI application."""


import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_config(tmp_path):
    """Create test config file."""
    config_file = tmp_path / "test_api.yaml"
    config_file.write_text(
        """
keys: []  # Open mode

cache:
  enabled: true
  max_size: 100
  ttl_seconds: 60

limits:
  default_daily_usd: 100.0
  default_rpm: 100
  default_tpm: 10000

fallback:
  max_attempts: 3
  timeout_seconds: 30

circuit_breaker:
  failure_threshold: 5
  cooldown_seconds: 60

models:
  - id: test-model
    provider: test
    cost_per_1m_input: 1.0
    cost_per_1m_output: 2.0
    avg_latency_ms: 500
    context_window: 100000
    quality_tier: 3
    capabilities: [tools, json]
"""
    )
    return config_file


def test_health_endpoint(test_config):
    """Test health endpoint."""
    from modelgate import api

    api.CONFIG_PATH = test_config
    client = TestClient(api.app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_models_endpoint(test_config):
    """Test models listing endpoint."""
    from modelgate import api

    api.CONFIG_PATH = test_config
    client = TestClient(api.app)

    response = client.get("/v1/models")
    assert response.status_code == 200

    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "test-model"


def test_chat_completions_endpoint(test_config):
    """Test chat completions endpoint."""
    from modelgate import api

    api.CONFIG_PATH = test_config
    # Reset globals
    api._catalog = None
    api._cache = None
    api._limits = None
    api._breaker = None
    api._router = None
    api._executor = None
    api._provider = None

    client = TestClient(api.app)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.7,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "id" in data
    assert data["object"] == "chat.completion"
    assert data["model"] == "test-model"
    assert len(data["choices"]) == 1
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert "usage" in data

    # Check custom headers
    assert "x-modelgate-model" in response.headers
    assert "x-modelgate-cost-usd" in response.headers
    assert "x-modelgate-attempts" in response.headers
    assert "x-modelgate-cache" in response.headers


def test_cache_hit_header(test_config):
    """Test cache hit header on repeated request."""
    from modelgate import api

    api.CONFIG_PATH = test_config
    api._catalog = None
    api._cache = None
    api._limits = None
    api._breaker = None
    api._router = None
    api._executor = None
    api._provider = None

    client = TestClient(api.app)

    request_data = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Test"}],
        "temperature": 0.7,
    }

    # First request - miss
    response1 = client.post("/v1/chat/completions", json=request_data)
    assert response1.status_code == 200
    assert response1.headers["x-modelgate-cache"] == "miss"

    # Second request - hit
    response2 = client.post("/v1/chat/completions", json=request_data)
    assert response2.status_code == 200
    assert response2.headers["x-modelgate-cache"] == "hit"


def test_no_route_returns_400(test_config):
    """Test that no route returns 400."""
    from modelgate import api

    api.CONFIG_PATH = test_config
    api._catalog = None
    api._cache = None
    api._limits = None
    api._breaker = None
    api._router = None
    api._executor = None
    api._provider = None

    client = TestClient(api.app)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "nonexistent",
            "messages": [{"role": "user", "content": "Test"}],
        },
    )

    assert response.status_code == 400


def test_metrics_endpoint(test_config):
    """Test metrics endpoint."""
    from modelgate import api

    api.CONFIG_PATH = test_config
    api._catalog = None
    api._cache = None
    api._limits = None
    api._breaker = None
    api._router = None
    api._executor = None
    api._provider = None

    client = TestClient(api.app)

    # Make a request first
    client.post(
        "/v1/chat/completions",
        json={
            "model": "test-model",
            "messages": [{"role": "user", "content": "Test"}],
        },
    )

    response = client.get("/metrics")
    assert response.status_code == 200

    data = response.json()
    assert "cache_size" in data
    assert "provider_calls" in data
    assert data["provider_calls"] >= 1


def test_usage_endpoint(test_config):
    """Test usage endpoint."""
    from modelgate import api

    api.CONFIG_PATH = test_config
    api._catalog = None
    api._cache = None
    api._limits = None
    api._breaker = None
    api._router = None
    api._executor = None
    api._provider = None

    client = TestClient(api.app)

    response = client.get("/v1/usage")
    assert response.status_code == 200

    data = response.json()
    assert "remaining_budget_usd" in data
