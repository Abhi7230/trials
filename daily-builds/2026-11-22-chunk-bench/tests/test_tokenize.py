"""Tests for tokenization."""

import pytest
from chunk_bench.tokenize import tokenize, count_tokens, truncate_to_tokens, split_by_sentences


def test_tokenize():
    """Test basic tokenization."""
    assert tokenize("hello world") == ["hello", "world"]
    assert tokenize("") == []
    assert tokenize("one") == ["one"]


def test_count_tokens():
    """Test token counting."""
    assert count_tokens("hello world") == 2
    assert count_tokens("") == 0
    assert count_tokens("one two three") == 3


def test_truncate_to_tokens():
    """Test truncating text to token limit."""
    text = "one two three four five"
    assert truncate_to_tokens(text, 3) == "one two three"
    assert truncate_to_tokens(text, 10) == text
    assert truncate_to_tokens("hello", 1) == "hello"


def test_split_by_sentences():
    """Test sentence splitting."""
    text = "First sentence. Second sentence! Third question?"
    sentences = split_by_sentences(text)
    assert len(sentences) == 3
    assert "First sentence." in sentences[0]
    
    assert split_by_sentences("") == []
    assert split_by_sentences("No punctuation") == ["No punctuation"]


def test_unicode_tokenization():
    """Test tokenization with unicode."""
    text = "Hello 世界 test"
    tokens = tokenize(text)
    assert len(tokens) == 3
