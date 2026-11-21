"""Tests for fuzzing generator."""

import pytest
from mcp_probe.fuzz import FuzzGenerator


def test_fuzz_generator_deterministic():
    """Test generator produces same results with same seed."""
    gen1 = FuzzGenerator(seed=42)
    gen2 = FuzzGenerator(seed=42)
    
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0, "maximum": 100}
        },
        "required": ["name"]
    }
    
    valid1 = gen1.generate_valid(schema, count=3)
    valid2 = gen2.generate_valid(schema, count=3)
    
    assert valid1 == valid2


def test_fuzz_generate_string():
    """Test string generation."""
    gen = FuzzGenerator(seed=1)
    schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "minLength": 5, "maxLength": 10}
        },
        "required": ["text"]
    }
    
    results = gen.generate_valid(schema, count=2)
    
    for result in results:
        assert "text" in result
        assert isinstance(result["text"], str)
        assert 5 <= len(result["text"]) <= 10


def test_fuzz_generate_integer():
    """Test integer generation."""
    gen = FuzzGenerator(seed=1)
    schema = {
        "type": "object",
        "properties": {
            "count": {"type": "integer", "minimum": 10, "maximum": 20}
        },
        "required": ["count"]
    }
    
    results = gen.generate_valid(schema, count=2)
    
    for result in results:
        assert "count" in result
        assert isinstance(result["count"], int)
        assert 10 <= result["count"] <= 20


def test_fuzz_generate_enum():
    """Test enum generation."""
    gen = FuzzGenerator(seed=1)
    schema = {
        "type": "object",
        "properties": {
            "choice": {"type": "string", "enum": ["a", "b", "c"]}
        },
        "required": ["choice"]
    }
    
    results = gen.generate_valid(schema, count=5)
    
    for result in results:
        assert "choice" in result
        assert result["choice"] in ["a", "b", "c"]


def test_fuzz_generate_array():
    """Test array generation."""
    gen = FuzzGenerator(seed=1)
    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 3
            }
        },
        "required": ["items"]
    }
    
    results = gen.generate_valid(schema, count=2)
    
    for result in results:
        assert "items" in result
        assert isinstance(result["items"], list)
        assert 1 <= len(result["items"]) <= 3


def test_fuzz_generate_invalid_missing_required():
    """Test generation of invalid input with missing required field."""
    gen = FuzzGenerator(seed=1)
    schema = {
        "type": "object",
        "properties": {
            "required_field": {"type": "string"},
            "optional_field": {"type": "string"}
        },
        "required": ["required_field"]
    }
    
    invalid = gen.generate_invalid(schema, count=4)
    
    assert any("required_field" not in item for item in invalid)


def test_fuzz_generate_invalid_wrong_type():
    """Test generation of invalid input with wrong type."""
    gen = FuzzGenerator(seed=1)
    schema = {
        "type": "object",
        "properties": {
            "number": {"type": "integer"}
        },
        "required": ["number"]
    }
    
    invalid = gen.generate_invalid(schema, count=4)
    
    assert any(
        "number" in item and not isinstance(item["number"], int)
        for item in invalid
    )


def test_fuzz_generate_invalid_extra_field():
    """Test generation of invalid input with extra field."""
    gen = FuzzGenerator(seed=1)
    schema = {
        "type": "object",
        "properties": {
            "field": {"type": "string"}
        },
        "required": ["field"]
    }
    
    invalid = gen.generate_invalid(schema, count=4)
    
    assert any("__extra_unexpected_field__" in item for item in invalid)


def test_fuzz_generate_invalid_huge_string():
    """Test generation of huge string input."""
    gen = FuzzGenerator(seed=1)
    schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "maxLength": 100}
        },
        "required": ["text"]
    }
    
    invalid = gen.generate_invalid(schema, count=5)
    
    assert any(
        "huge" in item and len(item.get("huge", "")) > 10000
        for item in invalid
    )
