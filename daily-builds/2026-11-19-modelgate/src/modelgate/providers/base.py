"""Base provider interface."""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ProviderResponse:
    """Provider response."""

    content: str
    input_tokens: int
    output_tokens: int


class ProviderError(Exception):
    """Provider error."""

    def __init__(self, message: str, retriable: bool = False):
        super().__init__(message)
        self.retriable = retriable


class Provider(Protocol):
    """Provider interface."""

    def complete(self, model_id: str, request: dict[str, Any]) -> ProviderResponse:
        """Complete a chat request."""
        ...
