"""Tests for CLI commands."""

import subprocess
from pathlib import Path


def test_models_command(tmp_path):
    """Test models command shows model list."""
    config_file = tmp_path / "test_models.yaml"
    config_file.write_text(
        """
models:
  - id: test-model
    provider: test
    cost_per_1m_input: 1.0
    cost_per_1m_output: 2.0
    avg_latency_ms: 500
    context_window: 10000
    quality_tier: 3
    capabilities: [json]
"""
    )

    result = subprocess.run(
        ["modelgate", "models", "--config", str(config_file)],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert "test-model" in result.stdout
    assert "test" in result.stdout


def test_route_command(tmp_path):
    """Test route command shows ranked candidates."""
    config_file = tmp_path / "test_route.yaml"
    config_file.write_text(
        """
models:
  - id: cheap
    provider: test
    cost_per_1m_input: 0.5
    cost_per_1m_output: 1.0
    avg_latency_ms: 500
    context_window: 10000
    quality_tier: 3
    capabilities: []
  - id: expensive
    provider: test
    cost_per_1m_input: 5.0
    cost_per_1m_output: 10.0
    avg_latency_ms: 300
    context_window: 10000
    quality_tier: 5
    capabilities: []
"""
    )

    result = subprocess.run(
        [
            "modelgate",
            "route",
            "test prompt",
            "--config",
            str(config_file),
            "--policy",
            "cheapest",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert "cheap" in result.stdout
    assert "expensive" in result.stdout
    assert "Ranked Candidates" in result.stdout


def test_simulate_command(tmp_path):
    """Test simulate command produces comparison."""
    config_file = tmp_path / "test_sim.yaml"
    config_file.write_text(
        """
models:
  - id: cheap
    provider: test
    cost_per_1m_input: 0.5
    cost_per_1m_output: 1.0
    avg_latency_ms: 500
    context_window: 100000
    quality_tier: 3
    capabilities: [json, tools]
  - id: expensive
    provider: test
    cost_per_1m_input: 5.0
    cost_per_1m_output: 10.0
    avg_latency_ms: 300
    context_window: 100000
    quality_tier: 5
    capabilities: [json, tools, vision]
"""
    )

    trace_file = tmp_path / "trace.jsonl"
    trace_file.write_text(
        '{"prompt_length": 100, "completion_length": 50, "capabilities": []}\n'
    )

    result = subprocess.run(
        [
            "modelgate",
            "simulate",
            str(trace_file),
            "--config",
            str(config_file),
            "--policy",
            "cheapest",
            "--policy",
            "balanced",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert "SIMULATION RESULTS" in result.stdout
    assert "cheapest" in result.stdout
    assert "balanced" in result.stdout


def test_bad_config_exits_2(tmp_path):
    """Test bad config exits with code 2."""
    bad_config = tmp_path / "bad.yaml"
    bad_config.write_text("invalid: yaml: : :")

    result = subprocess.run(
        ["modelgate", "models", "--config", str(bad_config)],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 2
