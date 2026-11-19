"""OpenAI-compatible HTTP provider."""

from typing import Any

import httpx

from modelgate.providers.base import ProviderError, ProviderResponse


class OpenAICompatProvider:
    """OpenAI-compatible HTTP provider."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.client = client or httpx.Client(timeout=timeout)

    def complete(self, model_id: str, request: dict[str, Any]) -> ProviderResponse:
        """Complete via OpenAI-compatible API."""
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model_id,
            **request,
            "stream": False,  # Force non-streaming
        }

        try:
            response = self.client.post(url, json=payload, headers=headers)

            if response.status_code == 429:
                raise ProviderError("Rate limit exceeded", retriable=True)

            if response.status_code >= 500:
                raise ProviderError(
                    f"Server error: {response.status_code}", retriable=True
                )

            if response.status_code != 200:
                raise ProviderError(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            return ProviderResponse(
                content=content,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
            )

        except httpx.TimeoutException as e:
            raise ProviderError(f"Timeout: {e}", retriable=True) from e
        except httpx.RequestError as e:
            raise ProviderError(f"Request error: {e}", retriable=True) from e
