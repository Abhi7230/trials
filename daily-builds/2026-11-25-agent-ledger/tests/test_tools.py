"""Tests for tool manifest."""

import pytest
from jsonschema import validate


def test_tools_endpoint(client):
    """Test /v1/tools endpoint."""
    response = client.get("/v1/tools")
    assert response.status_code == 200
    
    tools = response.json()
    assert isinstance(tools, list)
    assert len(tools) == 5
    
    tool_names = {t["name"] for t in tools}
    assert tool_names == {
        "send_money",
        "request_money",
        "split_bill",
        "get_balance",
        "list_transactions",
    }


def test_tool_schema_valid(client):
    """Test tool schemas are valid JSON Schema."""
    response = client.get("/v1/tools")
    tools = response.json()
    
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema


def test_send_money_schema(client):
    """Test send_money schema has required fields."""
    response = client.get("/v1/tools")
    tools = response.json()
    
    send_money = next(t for t in tools if t["name"] == "send_money")
    schema = send_money["inputSchema"]
    
    assert "required" in schema
    assert "to" in schema["required"]
    assert "amount_cents" in schema["required"]
