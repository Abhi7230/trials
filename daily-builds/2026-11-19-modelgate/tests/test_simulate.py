"""Tests for simulation."""

import json
from pathlib import Path

from modelgate.catalog import Catalog, Model
from modelgate.simulate import Simulator, format_results_json, format_results_table


def make_model(
    id: str,
    cost_in: float,
    cost_out: float,
    latency: float,
    quality: int,
) -> Model:
    """Helper to create test model."""
    return Model(
        id=id,
        provider="test",
        cost_per_1m_input=cost_in,
        cost_per_1m_output=cost_out,
        avg_latency_ms=latency,
        context_window=100000,
        quality_tier=quality,
        capabilities=frozenset(["tools", "json"]),
    )


def test_simulator_fixed_trace():
    """Test simulator gives exact expected results for fixed trace."""
    models = [
        make_model("cheap", 0.5, 1.0, 500, 3),
        make_model("expensive", 5.0, 10.0, 300, 5),
    ]

    catalog = Catalog(models)
    simulator = Simulator(catalog)

    # Create fixed trace
    trace_data = [
        {"prompt_length": 1000, "completion_length": 500, "capabilities": []},
        {"prompt_length": 2000, "completion_length": 1000, "capabilities": []},
    ]

    trace_file = Path("/tmp/test_trace.jsonl")
    with trace_file.open("w") as f:
        for item in trace_data:
            f.write(json.dumps(item) + "\n")

    trace = simulator.load_trace(trace_file)
    assert len(trace) == 2

    # Simulate with cheapest policy
    from modelgate.policies import CheapestPolicy

    result = simulator.simulate_policy(CheapestPolicy(), trace)

    # Should pick cheap model both times
    # Request 1: (1000/1e6 * 0.5) + (500/1e6 * 1.0) = 0.0005 + 0.0005 = 0.001
    # Request 2: (2000/1e6 * 0.5) + (1000/1e6 * 1.0) = 0.001 + 0.001 = 0.002
    # Total: 0.003
    assert abs(result.total_cost - 0.003) < 1e-6
    assert result.total_requests == 2
    assert result.failed_requests == 0


def test_cheapest_costs_less_than_quality():
    """Test that cheapest policy costs less than quality-first."""
    models = [
        make_model("cheap", 0.5, 1.0, 500, 2),
        make_model("expensive", 5.0, 10.0, 300, 5),
    ]

    catalog = Catalog(models)
    simulator = Simulator(catalog)

    trace_data = [
        {"prompt_length": 1000, "completion_length": 500, "capabilities": []},
        {"prompt_length": 1000, "completion_length": 500, "capabilities": []},
    ]

    trace_file = Path("/tmp/test_trace2.jsonl")
    with trace_file.open("w") as f:
        for item in trace_data:
            f.write(json.dumps(item) + "\n")

    trace = simulator.load_trace(trace_file)

    results = simulator.compare_policies(["cheapest", "quality-first"], trace)

    cheapest_result = next(r for r in results if r.policy_name == "cheapest")
    quality_result = next(r for r in results if r.policy_name == "quality-first")

    assert cheapest_result.total_cost < quality_result.total_cost


def test_savings_calculation():
    """Test savings percentage calculation."""
    models = [
        make_model("cheap", 0.5, 1.0, 500, 3),
        make_model("expensive", 10.0, 20.0, 300, 5),
    ]

    catalog = Catalog(models)
    simulator = Simulator(catalog)

    trace_data = [{"prompt_length": 1000, "completion_length": 1000, "capabilities": []}]

    trace_file = Path("/tmp/test_trace3.jsonl")
    with trace_file.open("w") as f:
        for item in trace_data:
            f.write(json.dumps(item) + "\n")

    trace = simulator.load_trace(trace_file)
    results = simulator.compare_policies(["cheapest", "quality-first"], trace)

    # Check that savings are calculated correctly
    table = format_results_table(results)
    assert "saves" in table
    assert "%" in table


def test_json_output_schema():
    """Test JSON output has expected schema."""
    models = [make_model("test", 1.0, 2.0, 500, 3)]
    catalog = Catalog(models)
    simulator = Simulator(catalog)

    trace_data = [{"prompt_length": 100, "completion_length": 50, "capabilities": []}]

    trace_file = Path("/tmp/test_trace4.jsonl")
    with trace_file.open("w") as f:
        for item in trace_data:
            f.write(json.dumps(item) + "\n")

    trace = simulator.load_trace(trace_file)
    results = simulator.compare_policies(["cheapest"], trace)

    json_output = format_results_json(results)
    data = json.loads(json_output)

    assert "results" in data
    assert len(data["results"]) == 1
    assert "policy" in data["results"][0]
    assert "total_cost_usd" in data["results"][0]
    assert "p50_latency_ms" in data["results"][0]


def test_svg_output_contains_table():
    """Test SVG/table output contains expected content."""
    models = [make_model("test", 1.0, 2.0, 500, 3)]
    catalog = Catalog(models)
    simulator = Simulator(catalog)

    trace_data = [{"prompt_length": 100, "completion_length": 50, "capabilities": []}]

    trace_file = Path("/tmp/test_trace5.jsonl")
    with trace_file.open("w") as f:
        for item in trace_data:
            f.write(json.dumps(item) + "\n")

    trace = simulator.load_trace(trace_file)
    results = simulator.compare_policies(["cheapest"], trace)

    table = format_results_table(results)

    assert "SIMULATION RESULTS" in table
    assert "Policy" in table
    assert "Cost ($)" in table
    assert "cheapest" in table
