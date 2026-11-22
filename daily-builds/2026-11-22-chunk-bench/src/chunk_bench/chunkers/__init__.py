"""Chunking strategies."""

from .fixed import FixedChunker
from .sentence import SentenceChunker
from .recursive import RecursiveChunker
from .markdown import MarkdownChunker

__all__ = ["FixedChunker", "SentenceChunker", "RecursiveChunker", "MarkdownChunker"]


def get_chunker(strategy: str, size: int, overlap: int = 0):
    """Get a chunker by strategy name."""
    if strategy == "fixed":
        return FixedChunker(chunk_size=size, overlap=overlap)
    elif strategy == "sentence":
        return SentenceChunker(sentences_per_chunk=size, overlap=overlap)
    elif strategy == "recursive":
        return RecursiveChunker(chunk_size=size, overlap=overlap)
    elif strategy == "markdown":
        return MarkdownChunker(max_chunk_size=size, overlap=overlap)
    else:
        raise ValueError(f"Unknown chunker strategy: {strategy}")
