"""Tests for FastAPI endpoint."""

import pytest
import json
from fastapi.testclient import TestClient
from mcp_probe.api import app

client = TestClient(app)


def test_api_root():
    """Test API root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()


def test_api_get_rules():
    """Test GET /rules endpoint."""
    response = client.get("/rules")
    assert response.status_code == 200
    
    rules = response.json()
    assert isinstance(rules, list)
    assert len(rules) > 0
    assert "rule_ids" in rules[0]
    assert "category" in rules[0]


def test_api_check_transcript():
    """Test POST /check-transcript endpoint."""
    transcript_data = {
        "type": "response",
        "data": {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "A test tool with valid schema",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "param": {"type": "string", "description": "Test parameter"}
                            }
                        }
                    }
                ]
            }
        }
    }
    
    response = client.post(
        "/check-transcript",
        json={"transcript": json.dumps(transcript_data)}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "score" in result
    assert "grade" in result
    assert "findings" in result


def test_api_check_transcript_invalid():
    """Test POST /check-transcript with invalid data."""
    response = client.post(
        "/check-transcript",
        json={"transcript": "invalid json{{{"}
    )
    
    assert response.status_code == 400
