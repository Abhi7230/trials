"""Tests for API."""

from fastapi.testclient import TestClient

from skill_lint.api import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rules_endpoint() -> None:
    """Test rules listing endpoint."""
    response = client.get("/rules")
    
    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    assert len(data["rules"]) == 11


def test_lint_endpoint_valid() -> None:
    """Test lint endpoint with valid content."""
    content = """---
name: test-skill
description: A test skill for the API endpoint that helps when you need to test linting
---

# Test Skill

```python
print("example")
```
"""
    
    response = client.post("/lint", json={"content": content})
    
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert "findings" in data
    assert "scores" in data


def test_lint_endpoint_invalid() -> None:
    """Test lint endpoint with invalid content."""
    content = "# No frontmatter\n\nThis will have errors."
    
    response = client.post("/lint", json={"content": content})
    
    assert response.status_code == 200
    data = response.json()
    assert "findings" in data
    # Should have findings for missing frontmatter
    findings = list(data["findings"].values())[0]
    assert len(findings) > 0


def test_lint_endpoint_missing_content() -> None:
    """Test lint endpoint with missing content."""
    response = client.post("/lint", json={})
    
    assert response.status_code == 422  # Validation error
