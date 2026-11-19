"""Tests for catalog module."""

import pytest
import yaml

from modelgate.catalog import Catalog, Model
from modelgate.config import Config, load_config


def test_load_valid_config(tmp_path):
    """Test loading valid YAML config."""
    config_file = tmp_path / "models.yaml"
    config_file.write_text(
        """
models:
  - id: gpt-4
    provider: openai
    cost_per_1m_input: 30.0
    cost_per_1m_output: 60.0
    avg_latency_ms: 1000
    context_window: 128000
    quality_tier: 5
    capabilities: [tools, json]
"""
    )

    cfg = load_config(config_file)
    assert len(cfg.models) == 1
    assert cfg.models[0].id == "gpt-4"


def test_invalid_cost_raises_error(tmp_path):
    """Test that invalid cost raises validation error."""
    config_file = tmp_path / "models.yaml"
    config_file.write_text(
        """
models:
  - id: bad-model
    provider: test
    cost_per_1m_input: -1.0
    cost_per_1m_output: 10.0
    avg_latency_ms: 500
    context_window: 1000
    quality_tier: 3
"""
    )

    with pytest.raises(Exception):  # pydantic ValidationError
        load_config(config_file)


def test_missing_field_raises_error(tmp_path):
    """Test that missing required field raises error."""
    config_file = tmp_path / "models.yaml"
    config_file.write_text(
        """
models:
  - id: incomplete
    provider: test
    cost_per_1m_input: 1.0
"""
    )

    with pytest.raises(Exception):
        load_config(config_file)


def test_duplicate_ids_rejected(tmp_path):
    """Test that duplicate model IDs are rejected."""
    config_file = tmp_path / "models.yaml"
    config_file.write_text(
        """
models:
  - id: duplicate
    provider: test1
    cost_per_1m_input: 1.0
    cost_per_1m_output: 2.0
    avg_latency_ms: 100
    context_window: 1000
    quality_tier: 3
  - id: duplicate
    provider: test2
    cost_per_1m_input: 1.0
    cost_per_1m_output: 2.0
    avg_latency_ms: 100
    context_window: 1000
    quality_tier: 3
"""
    )

    with pytest.raises(Exception, match="Duplicate"):
        load_config(config_file)


def test_catalog_filter_by_context():
    """Test filtering by context window."""
    models = [
        Model(
            id="small",
            provider="test",
            cost_per_1m_input=1.0,
            cost_per_1m_output=2.0,
            avg_latency_ms=100,
            context_window=1000,
            quality_tier=3,
            capabilities=frozenset(),
        ),
        Model(
            id="large",
            provider="test",
            cost_per_1m_input=2.0,
            cost_per_1m_output=4.0,
            avg_latency_ms=200,
            context_window=10000,
            quality_tier=4,
            capabilities=frozenset(),
        ),
    ]

    catalog = Catalog(models)
    filtered = catalog.filter(min_context=5000)

    assert len(filtered) == 1
    assert filtered[0].id == "large"


def test_catalog_filter_by_capabilities():
    """Test filtering by required capabilities."""
    models = [
        Model(
            id="basic",
            provider="test",
            cost_per_1m_input=1.0,
            cost_per_1m_output=2.0,
            avg_latency_ms=100,
            context_window=1000,
            quality_tier=3,
            capabilities=frozenset(["json"]),
        ),
        Model(
            id="advanced",
            provider="test",
            cost_per_1m_input=2.0,
            cost_per_1m_output=4.0,
            avg_latency_ms=200,
            context_window=1000,
            quality_tier=4,
            capabilities=frozenset(["json", "tools", "vision"]),
        ),
    ]

    catalog = Catalog(models)
    filtered = catalog.filter(required_capabilities=frozenset(["tools"]))

    assert len(filtered) == 1
    assert filtered[0].id == "advanced"
