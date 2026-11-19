"""Tests for router module."""

import pytest

from modelgate.catalog import Catalog, Model
from modelgate.router import NoRouteError, Router, RoutingRequest
from modelgate.tokens import SimpleTokenizer


def make_model(
    id: str,
    context: int = 10000,
    capabilities: list[str] | None = None,
) -> Model:
    """Helper to create test model."""
    return Model(
        id=id,
        provider="test",
        cost_per_1m_input=1.0,
        cost_per_1m_output=2.0,
        avg_latency_ms=500,
        context_window=context,
        quality_tier=3,
        capabilities=frozenset(capabilities or []),
    )


def test_explicit_model_bypasses_policy():
    """Test that explicit model name bypasses routing policy."""
    models = [
        make_model("model-a"),
        make_model("model-b"),
    ]

    catalog = Catalog(models)
    router = Router(catalog, SimpleTokenizer())

    request = RoutingRequest(
        model="model-b",
        messages=[{"role": "user", "content": "test"}],
    )

    candidates = router.route(request)
    assert len(candidates) == 1
    assert candidates[0].id == "model-b"


def test_unknown_explicit_model_raises():
    """Test that unknown model raises NoRouteError."""
    models = [make_model("model-a")]
    catalog = Catalog(models)
    router = Router(catalog, SimpleTokenizer())

    request = RoutingRequest(
        model="nonexistent",
        messages=[{"role": "user", "content": "test"}],
    )

    with pytest.raises(NoRouteError, match="not found"):
        router.route(request)


def test_context_window_filtering():
    """Test that small-window models are excluded for large context."""
    models = [
        make_model("small", context=1000),
        make_model("large", context=100000),
    ]

    catalog = Catalog(models)
    router = Router(catalog, SimpleTokenizer())

    # Large message that needs big context
    large_content = "x" * 10000  # ~2500 tokens
    request = RoutingRequest(
        model="auto",
        messages=[{"role": "user", "content": large_content}],
    )

    candidates = router.route(request)
    assert all(c.context_window >= 3000 for c in candidates)
    assert candidates[0].id == "large"


def test_capability_filtering():
    """Test that models without required capabilities are excluded."""
    models = [
        make_model("basic", capabilities=[]),
        make_model("with-tools", capabilities=["tools"]),
        make_model("with-vision", capabilities=["vision"]),
        make_model("full-featured", capabilities=["tools", "vision", "json"]),
    ]

    catalog = Catalog(models)
    router = Router(catalog, SimpleTokenizer())

    request = RoutingRequest(
        model="auto",
        messages=[{"role": "user", "content": "test"}],
        required_capabilities=frozenset(["tools", "vision"]),
    )

    candidates = router.route(request)
    assert len(candidates) == 1
    assert candidates[0].id == "full-featured"


def test_no_candidates_raises():
    """Test that no matching candidates raises NoRouteError."""
    models = [
        make_model("basic", context=1000, capabilities=[]),
    ]

    catalog = Catalog(models)
    router = Router(catalog, SimpleTokenizer())

    request = RoutingRequest(
        model="auto",
        messages=[{"role": "user", "content": "test"}],
        required_capabilities=frozenset(["vision"]),
    )

    with pytest.raises(NoRouteError, match="No models found"):
        router.route(request)


def test_auto_with_policy():
    """Test auto:policy syntax."""
    expensive = Model(
        id="expensive",
        provider="test",
        cost_per_1m_input=10.0,
        cost_per_1m_output=20.0,
        avg_latency_ms=500,
        context_window=10000,
        quality_tier=5,
        capabilities=frozenset(),
    )
    cheap = Model(
        id="cheap",
        provider="test",
        cost_per_1m_input=0.5,
        cost_per_1m_output=1.0,
        avg_latency_ms=500,
        context_window=10000,
        quality_tier=3,
        capabilities=frozenset(),
    )

    catalog = Catalog([expensive, cheap])
    router = Router(catalog, SimpleTokenizer())

    request = RoutingRequest(
        model="auto:cheapest",
        messages=[{"role": "user", "content": "test"}],
    )

    candidates = router.route(request)
    assert candidates[0].id == "cheap"


def test_policy_header_override():
    """Test x-modelgate-policy header override."""
    slow = Model(
        id="slow",
        provider="test",
        cost_per_1m_input=1.0,
        cost_per_1m_output=2.0,
        avg_latency_ms=1000,
        context_window=10000,
        quality_tier=3,
        capabilities=frozenset(),
    )
    fast = Model(
        id="fast",
        provider="test",
        cost_per_1m_input=1.0,
        cost_per_1m_output=2.0,
        avg_latency_ms=100,
        context_window=10000,
        quality_tier=3,
        capabilities=frozenset(),
    )

    catalog = Catalog([slow, fast])
    router = Router(catalog, SimpleTokenizer(), default_policy="cheapest")

    request = RoutingRequest(
        model="auto",
        messages=[{"role": "user", "content": "test"}],
        policy_override="fastest",
    )

    candidates = router.route(request)
    assert candidates[0].id == "fast"
