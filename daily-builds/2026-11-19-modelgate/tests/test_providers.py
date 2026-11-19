"""Tests for provider implementations."""

import pytest
import httpx

from modelgate.providers.base import ProviderError
from modelgate.providers.mock import MockProvider
from modelgate.providers.openai_compat import OpenAICompatProvider


def test_mock_provider_deterministic():
    """Test mock provider gives deterministic output."""
    provider = MockProvider(latency_ms=0)

    request = {"messages": [{"role": "user", "content": "test"}]}

    response1 = provider.complete("model-a", request)
    response2 = provider.complete("model-a", request)

    # Same request should give same response
    assert response1.content == response2.content


def test_mock_provider_different_models():
    """Test mock provider differs by model."""
    provider = MockProvider(latency_ms=0)

    request = {"messages": [{"role": "user", "content": "test"}]}

    resp_a = provider.complete("model-a", request)
    resp_b = provider.complete("model-b", request)

    # Different models should give different responses
    assert resp_a.content != resp_b.content


def test_mock_provider_failure_injection():
    """Test mock provider failure injection."""
    provider = MockProvider(latency_ms=0, failure_rate=1.0, failure_retriable=True)

    request = {"messages": [{"role": "user", "content": "test"}]}

    with pytest.raises(ProviderError) as exc_info:
        provider.complete("model-a", request)

    assert exc_info.value.retriable


def test_mock_provider_counts_calls():
    """Test mock provider tracks call count."""
    provider = MockProvider(latency_ms=0)

    request = {"messages": []}

    assert provider.call_count == 0
    provider.complete("model-a", request)
    assert provider.call_count == 1
    provider.complete("model-a", request)
    assert provider.call_count == 2


def test_openai_compat_success():
    """Test OpenAI-compatible provider with successful response."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-123",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Hello!"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)

    provider = OpenAICompatProvider(
        base_url="https://api.test.com",
        api_key="test-key",
        client=client,
    )

    request = {"messages": [{"role": "user", "content": "Hi"}]}
    response = provider.complete("gpt-4", request)

    assert response.content == "Hello!"
    assert response.input_tokens == 10
    assert response.output_tokens == 5


def test_openai_compat_maps_429_to_retriable():
    """Test that 429 is mapped to retriable error."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "Rate limit"}})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)

    provider = OpenAICompatProvider(
        base_url="https://api.test.com",
        api_key="test-key",
        client=client,
    )

    request = {"messages": []}

    with pytest.raises(ProviderError) as exc_info:
        provider.complete("gpt-4", request)

    assert exc_info.value.retriable
    assert "Rate limit" in str(exc_info.value)


def test_openai_compat_maps_500_to_retriable():
    """Test that 500 is mapped to retriable error."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal error")

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)

    provider = OpenAICompatProvider(
        base_url="https://api.test.com",
        api_key="test-key",
        client=client,
    )

    request = {"messages": []}

    with pytest.raises(ProviderError) as exc_info:
        provider.complete("gpt-4", request)

    assert exc_info.value.retriable
    assert "500" in str(exc_info.value)
