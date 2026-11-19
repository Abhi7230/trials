"""Tests for executor with fallback."""

import pytest

from modelgate.breaker import CircuitBreaker
from modelgate.catalog import Model
from modelgate.executor import ExecutionError, Executor
from modelgate.providers.base import ProviderError, ProviderResponse


class FakeProvider:
    """Fake provider for testing."""

    def __init__(self):
        self.calls = []
        self.responses = {}
        self.failures = {}

    def complete(self, model_id: str, request: dict) -> ProviderResponse:
        """Complete with configured response or failure."""
        self.calls.append(model_id)

        if model_id in self.failures:
            raise self.failures[model_id]

        if model_id in self.responses:
            return self.responses[model_id]

        return ProviderResponse(
            content=f"Response from {model_id}", input_tokens=10, output_tokens=20
        )


def make_model(id: str) -> Model:
    """Helper to create test model."""
    return Model(
        id=id,
        provider="test",
        cost_per_1m_input=1.0,
        cost_per_1m_output=2.0,
        avg_latency_ms=100,
        context_window=10000,
        quality_tier=3,
        capabilities=frozenset(),
    )


def test_executor_success_on_first_attempt():
    """Test successful execution on first attempt."""
    provider = FakeProvider()
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)
    executor = Executor(provider, breaker, max_attempts=3, timeout=10.0)

    models = [make_model("model-a"), make_model("model-b")]
    request = {"messages": [{"role": "user", "content": "test"}]}

    result = executor.execute(models, request)

    assert result.model.id == "model-a"
    assert result.attempts == 1
    assert len(result.errors) == 0
    assert len(provider.calls) == 1


def test_executor_fallback_on_first_failure():
    """Test fallback to second model on first failure."""
    provider = FakeProvider()
    provider.failures["model-a"] = ProviderError("Failed", retriable=True)

    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)
    executor = Executor(provider, breaker, max_attempts=3, timeout=10.0)

    models = [make_model("model-a"), make_model("model-b")]
    request = {"messages": []}

    result = executor.execute(models, request)

    assert result.model.id == "model-b"
    assert result.attempts == 2
    assert len(result.errors) == 1
    assert "model-a" in result.errors[0]


def test_executor_all_attempts_fail():
    """Test that all attempts failing raises ExecutionError."""
    provider = FakeProvider()
    provider.failures["model-a"] = ProviderError("Fail A", retriable=True)
    provider.failures["model-b"] = ProviderError("Fail B", retriable=True)

    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)
    executor = Executor(provider, breaker, max_attempts=3, timeout=10.0)

    models = [make_model("model-a"), make_model("model-b")]
    request = {"messages": []}

    with pytest.raises(ExecutionError) as exc_info:
        executor.execute(models, request)

    assert exc_info.value.attempts == 2
    assert len(exc_info.value.errors) == 2


def test_executor_respects_max_attempts():
    """Test that max_attempts is respected."""
    provider = FakeProvider()
    provider.failures["model-a"] = ProviderError("Fail", retriable=True)
    provider.failures["model-b"] = ProviderError("Fail", retriable=True)
    provider.failures["model-c"] = ProviderError("Fail", retriable=True)

    breaker = CircuitBreaker(failure_threshold=5, cooldown_seconds=60)
    executor = Executor(provider, breaker, max_attempts=2, timeout=10.0)

    models = [make_model("model-a"), make_model("model-b"), make_model("model-c")]
    request = {"messages": []}

    with pytest.raises(ExecutionError) as exc_info:
        executor.execute(models, request)

    # Should only try 2 models
    assert exc_info.value.attempts == 2


def test_executor_skips_open_breaker():
    """Test that models with open breaker are skipped."""
    provider = FakeProvider()
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=60)
    executor = Executor(provider, breaker, max_attempts=3, timeout=10.0)

    # Open breaker for model-a
    breaker.record_failure("model-a")
    breaker.record_failure("model-a")

    models = [make_model("model-a"), make_model("model-b")]
    request = {"messages": []}

    result = executor.execute(models, request)

    # Should skip model-a and use model-b
    assert result.model.id == "model-b"
    assert result.attempts == 1
    assert "circuit breaker open" in result.errors[0]


def test_executor_non_retriable_error_stops_fallback():
    """Test that non-retriable error stops fallback chain."""
    provider = FakeProvider()
    provider.failures["model-a"] = ProviderError("Fatal error", retriable=False)

    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)
    executor = Executor(provider, breaker, max_attempts=3, timeout=10.0)

    models = [make_model("model-a"), make_model("model-b")]
    request = {"messages": []}

    with pytest.raises(ExecutionError, match="Non-retriable"):
        executor.execute(models, request)

    # Should not have tried model-b
    assert len(provider.calls) == 1
