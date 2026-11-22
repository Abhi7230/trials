"""Whitespace tokenizer with deterministic token counting."""

import re


def tokenize(text: str) -> list[str]:
    """Tokenize text by whitespace."""
    return text.split()


def count_tokens(text: str) -> int:
    """Count tokens in text."""
    return len(tokenize(text))


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to a maximum number of tokens."""
    tokens = tokenize(text)
    if len(tokens) <= max_tokens:
        return text
    return " ".join(tokens[:max_tokens])


def split_by_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    pattern = r'(?<=[.!?])\s+'
    sentences = re.split(pattern, text)
    return [s.strip() for s in sentences if s.strip()]
