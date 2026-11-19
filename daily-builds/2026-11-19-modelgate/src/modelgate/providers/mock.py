"""Mock provider for testing."""

import hashlib
from typing import Any

from modelgate.providers.base import ProviderError, ProviderResponse


class MockProvider:
    """Deterministic mock provider."""

    def __init__(
        self,
        latency_ms: float = 100,
        failure_rate: float = 0.0,
        failure_retriable: bool = False,
    ):
        self.latency_ms = latency_ms
        self.failure_rate = failure_rate
        self.failure_retriable = failure_retriable
        self.call_count = 0

    def complete(self, model_id: str, request: dict[str, Any]) -> ProviderResponse:
        """Complete with deterministic mock response."""
        import time

        self.call_count += 1

        # Simulate latency
        if self.latency_ms > 0:
            time.sleep(self.latency_ms / 1000.0)

        # Deterministic failure based on request hash
        if self.failure_rate > 0:
            request_str = str(sorted(request.items()))
            request_hash = int(hashlib.md5(request_str.encode()).hexdigest()[:8], 16)
            if (request_hash % 100) < (self.failure_rate * 100):
                raise ProviderError(
                    f"Mock failure for {model_id}", retriable=self.failure_retriable
                )

        # Generate deterministic response
        messages = request.get("messages", [])
        prompt = " ".join(msg.get("content", "") for msg in messages)
        response_hash = hashlib.md5(f"{model_id}:{prompt}".encode()).hexdigest()[:16]
        content = f"Mock response [{model_id}]: {response_hash}"

        # Estimate tokens
        input_tokens = max(10, len(prompt) // 4)
        output_tokens = len(content) // 4

        return ProviderResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
