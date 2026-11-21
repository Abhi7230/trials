"""Tests for result conformance rules."""

import pytest
from mcp_probe.rules.results import check_results
from mcp_probe.models import Severity


def test_valid_text_content():
    """Test valid text content passes."""
    result = {
        "content": [
            {"type": "text", "text": "Hello world"}
        ]
    }
    
    findings = check_results("test_tool", result)
    errors = [f for f in findings if f.severity == Severity.ERROR]
    assert len(errors) == 0


def test_content_not_list():
    """Test content must be a list."""
    result = {
        "content": "should be a list"
    }
    
    findings = check_results("test_tool", result)
    assert any(f.rule_id == "RS002" for f in findings)


def test_content_item_not_dict():
    """Test content items must be dicts."""
    result = {
        "content": ["string item", "another string"]
    }
    
    findings = check_results("test_tool", result)
    assert any(f.rule_id == "RS003" for f in findings)


def test_content_item_missing_type():
    """Test content items must have type."""
    result = {
        "content": [
            {"data": "missing type field"}
        ]
    }
    
    findings = check_results("test_tool", result)
    assert any(f.rule_id == "RS004" for f in findings)


def test_text_content_missing_text_field():
    """Test text content must have text field."""
    result = {
        "content": [
            {"type": "text"}
        ]
    }
    
    findings = check_results("test_tool", result)
    assert any(f.rule_id == "RS005" for f in findings)


def test_text_content_text_not_string():
    """Test text field must be string."""
    result = {
        "content": [
            {"type": "text", "text": 12345}
        ]
    }
    
    findings = check_results("test_tool", result)
    assert any(f.rule_id == "RS006" for f in findings)


def test_error_result():
    """Test error results are checked."""
    result = {
        "isError": True,
        "content": [{"type": "text", "text": "Error message"}]
    }
    
    findings = check_results("test_tool", result)
    errors = [f for f in findings if f.severity == Severity.ERROR]
    assert len(errors) == 0


def test_structured_content_validation():
    """Test structuredContent is validated against schema."""
    output_schema = {
        "type": "object",
        "properties": {
            "value": {"type": "integer"}
        },
        "required": ["value"]
    }
    
    result = {
        "structuredContent": {"value": "not an integer"}
    }
    
    findings = check_results("test_tool", result, output_schema)
    assert any(f.rule_id == "RS007" for f in findings)
