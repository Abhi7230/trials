"""Tests for API."""

from fastapi.testclient import TestClient

from agentlens.api import app

client = TestClient(app)


def test_analyze_returns_score() -> None:
    """Test /analyze endpoint returns a score."""
    response = client.post(
        "/analyze",
        json={
            "trace": [
                {"timestamp": "t1", "type": "message", "role": "user", "content": "Hello"},
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert data["score"] == 100


def test_analyze_fail_under() -> None:
    """Test fail_under option."""
    response = client.post(
        "/analyze",
        json={
            "trace": [
                {"timestamp": "t1", "type": "tool_result", "role": "tool", "error": "Failed"},
                {"timestamp": "t2", "type": "message", "role": "assistant", "content": "Done!"},
            ],
            "options": {"fail_under": 80},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False


def test_rules_endpoint() -> None:
    """Test /rules endpoint."""
    response = client.get("/rules")
    assert response.status_code == 200
    rules = response.json()
    assert len(rules) > 0
    assert "pattern_type" in rules[0]


def test_health_endpoint() -> None:
    """Test /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics_endpoint() -> None:
    """Test /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "analyses_count" in data
    assert "avg_score" in data
