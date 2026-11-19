"""Tests for routing policies."""

from modelgate.catalog import Model
from modelgate.policies import BalancedPolicy, CheapestPolicy, FastestPolicy, QualityFirstPolicy


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
        context_window=10000,
        quality_tier=quality,
        capabilities=frozenset(),
    )


def test_cheapest_policy():
    """Test cheapest policy picks lowest cost."""
    models = [
        make_model("expensive", 10.0, 20.0, 500, 5),
        make_model("cheap", 0.5, 1.0, 1000, 3),
        make_model("medium", 2.0, 4.0, 700, 4),
    ]

    policy = CheapestPolicy()
    ranked = policy.rank(models, input_tokens=1000, output_tokens=500)

    assert ranked[0][0].id == "cheap"
    assert ranked[1][0].id == "medium"
    assert ranked[2][0].id == "expensive"


def test_fastest_policy():
    """Test fastest policy picks lowest latency."""
    models = [
        make_model("slow", 1.0, 2.0, 1000, 5),
        make_model("fast", 2.0, 4.0, 100, 3),
        make_model("medium", 1.5, 3.0, 500, 4),
    ]

    policy = FastestPolicy()
    ranked = policy.rank(models, input_tokens=1000, output_tokens=500)

    assert ranked[0][0].id == "fast"
    assert ranked[1][0].id == "medium"
    assert ranked[2][0].id == "slow"


def test_quality_first_policy():
    """Test quality-first picks highest tier, then lowest cost."""
    models = [
        make_model("high-quality-expensive", 10.0, 20.0, 500, 5),
        make_model("high-quality-cheap", 1.0, 2.0, 600, 5),
        make_model("low-quality", 0.1, 0.2, 200, 2),
    ]

    policy = QualityFirstPolicy()
    ranked = policy.rank(models, input_tokens=1000, output_tokens=500)

    # Both tier 5, but cheap should win
    assert ranked[0][0].id == "high-quality-cheap"
    assert ranked[1][0].id == "high-quality-expensive"
    assert ranked[2][0].id == "low-quality"


def test_balanced_policy():
    """Test balanced policy weights factors."""
    models = [
        make_model("cheap-slow-low", 0.5, 1.0, 2000, 2),
        make_model("expensive-fast-high", 10.0, 20.0, 100, 5),
        make_model("balanced", 2.0, 4.0, 500, 4),
    ]

    policy = BalancedPolicy(cost_weight=0.4, latency_weight=0.3, quality_weight=0.3)
    ranked = policy.rank(models, input_tokens=1000, output_tokens=500)

    # Balanced should typically win with these weights
    assert ranked[0][0].id == "balanced"


def test_policy_deterministic_ties():
    """Test that ties are broken deterministically by ID."""
    models = [
        make_model("model-z", 1.0, 2.0, 500, 3),
        make_model("model-a", 1.0, 2.0, 500, 3),
        make_model("model-m", 1.0, 2.0, 500, 3),
    ]

    policy = CheapestPolicy()
    ranked = policy.rank(models, input_tokens=1000, output_tokens=500)

    # Should be sorted by ID when costs are equal
    assert ranked[0][0].id == "model-a"
    assert ranked[1][0].id == "model-m"
    assert ranked[2][0].id == "model-z"


def test_balanced_weights_affect_ranking():
    """Test that changing balanced weights changes ranking."""
    models = [
        make_model("cheap-slow", 0.5, 1.0, 2000, 3),
        make_model("expensive-fast", 5.0, 10.0, 100, 4),
    ]

    # Cost-heavy
    cost_heavy = BalancedPolicy(cost_weight=0.8, latency_weight=0.1, quality_weight=0.1)
    ranked_cost = cost_heavy.rank(models, input_tokens=1000, output_tokens=500)
    assert ranked_cost[0][0].id == "cheap-slow"

    # Latency-heavy
    latency_heavy = BalancedPolicy(cost_weight=0.1, latency_weight=0.8, quality_weight=0.1)
    ranked_latency = latency_heavy.rank(models, input_tokens=1000, output_tokens=500)
    assert ranked_latency[0][0].id == "expensive-fast"
