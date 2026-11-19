"""Token estimation."""

from typing import Protocol


class Tokenizer(Protocol):
    """Token counting interface."""

    def estimate(self, text: str) -> int:
        """Estimate token count for text."""
        ...


class SimpleTokenizer:
    """Simple character-based token estimator."""

    def estimate(self, text: str) -> int:
        """Estimate tokens as length / 4."""
        return max(1, len(text) // 4)
