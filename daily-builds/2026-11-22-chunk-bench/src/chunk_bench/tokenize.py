"""Whitespace tokenizer with deterministic token counting."""

import re
import string


def tokenize(text: str) -> list[str]:
    """Tokenize text by whitespace."""
    return text.split()


def tokenize_for_retrieval(text: str) -> list[str]:
    """Tokenize text for retrieval (lowercase, punctuation removed, basic stemming)."""
    text = text.lower()
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    tokens = text.split()
    
    stemmed = []
    for token in tokens:
        if len(token) > 4:
            if token.endswith('s') and not token.endswith('ss') and not token.endswith('us') and not token.endswith('is'):
                stemmed.append(token[:-1])
            elif token.endswith('ed') and not token.endswith('ted'):
                stemmed.append(token[:-1])
            else:
                stemmed.append(token)
        else:
            stemmed.append(token)
    
    return stemmed


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
