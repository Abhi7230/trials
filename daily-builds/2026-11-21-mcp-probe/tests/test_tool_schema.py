"""Tests for tool schema rules."""

import pytest
from mcp_probe.models import ToolInfo, Severity
from mcp_probe.rules.tool_schema import check_tool_schemas


def test_valid_tool_schema():
    """Test valid tool produces no errors."""
    tools = [
        ToolInfo(
            name="test_tool",
            description="A valid tool with proper description length",
            inputSchema={
                "type": "object",
                "properties": {
                    "param": {"type": "string", "description": "A parameter"}
                },
                "required": ["param"]
            }
        )
    ]
    
    findings = check_tool_schemas(tools)
    errors = [f for f in findings if f.severity == Severity.ERROR]
    assert len(errors) == 0


def test_duplicate_tool_names():
    """Test duplicate tool names are detected."""
    tools = [
        ToolInfo(
            name="duplicate",
            description="First tool with this name for testing",
            inputSchema={"type": "object"}
        ),
        ToolInfo(
            name="duplicate",
            description="Second tool with same name for testing",
            inputSchema={"type": "object"}
        )
    ]
    
    findings = check_tool_schemas(tools)
    assert any(f.rule_id == "TS001" for f in findings)


def test_invalid_tool_name():
    """Test invalid tool name is detected."""
    tools = [
        ToolInfo(
            name="bad name with spaces",
            description="Tool with invalid name format for testing",
            inputSchema={"type": "object"}
        )
    ]
    
    findings = check_tool_schemas(tools)
    assert any(f.rule_id == "TS002" for f in findings)


def test_empty_description():
    """Test empty description is detected."""
    tools = [
        ToolInfo(
            name="test",
            description="",
            inputSchema={"type": "object"}
        )
    ]
    
    findings = check_tool_schemas(tools)
    assert any(f.rule_id == "TS003" for f in findings)


def test_short_description():
    """Test short description generates warning."""
    tools = [
        ToolInfo(
            name="test",
            description="short",
            inputSchema={"type": "object"}
        )
    ]
    
    findings = check_tool_schemas(tools)
    assert any(f.rule_id == "TS004" and f.severity == Severity.WARNING for f in findings)


def test_required_field_not_in_properties():
    """Test required field not in properties is detected."""
    tools = [
        ToolInfo(
            name="test",
            description="Tool with mismatched required fields for testing",
            inputSchema={
                "type": "object",
                "properties": {
                    "field": {"type": "string"}
                },
                "required": ["missing_field"]
            }
        )
    ]
    
    findings = check_tool_schemas(tools)
    assert any(f.rule_id == "TS009" for f in findings)


def test_property_missing_type():
    """Test property missing type generates warning."""
    tools = [
        ToolInfo(
            name="test",
            description="Tool with property missing type for testing",
            inputSchema={
                "type": "object",
                "properties": {
                    "field": {"description": "A field"}
                }
            }
        )
    ]
    
    findings = check_tool_schemas(tools)
    assert any(f.rule_id == "TS007" and f.severity == Severity.WARNING for f in findings)


def test_empty_enum():
    """Test empty enum is detected."""
    tools = [
        ToolInfo(
            name="test",
            description="Tool with empty enum for testing validation",
            inputSchema={
                "type": "object",
                "properties": {
                    "field": {"type": "string", "enum": []}
                }
            }
        )
    ]
    
    findings = check_tool_schemas(tools)
    assert any(f.rule_id == "TS011" for f in findings)


def test_additional_properties_info():
    """Test missing additionalProperties generates info."""
    tools = [
        ToolInfo(
            name="test",
            description="Tool without additionalProperties specified for testing",
            inputSchema={
                "type": "object",
                "properties": {
                    "field": {"type": "string", "description": "A field"}
                }
            }
        )
    ]
    
    findings = check_tool_schemas(tools)
    assert any(f.rule_id == "TS010" and f.severity == Severity.INFO for f in findings)
