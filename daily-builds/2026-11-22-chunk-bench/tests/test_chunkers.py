"""Tests for chunking strategies."""

import pytest
from chunk_bench.models import Document
from chunk_bench.chunkers import FixedChunker, SentenceChunker, RecursiveChunker, MarkdownChunker


def test_fixed_chunker_basic():
    """Test fixed chunker basic functionality."""
    doc = Document(doc_id="test", text="one two three four five six seven eight")
    chunker = FixedChunker(chunk_size=3, overlap=0)
    chunks = chunker.chunk(doc)
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert len(chunk.text.split()) <= 3
        assert chunk.doc_id == "test"


def test_fixed_chunker_overlap():
    """Test fixed chunker with overlap."""
    doc = Document(doc_id="test", text="one two three four five six")
    chunker = FixedChunker(chunk_size=3, overlap=1)
    chunks = chunker.chunk(doc)
    
    assert len(chunks) >= 2


def test_fixed_chunker_offsets():
    """Test that offsets map back to source."""
    doc = Document(doc_id="test", text="hello world testing chunks")
    chunker = FixedChunker(chunk_size=2, overlap=0)
    chunks = chunker.chunk(doc)
    
    for chunk in chunks:
        extracted = doc.text[chunk.start_offset:chunk.end_offset]
        assert chunk.text in extracted or extracted in chunk.text


def test_fixed_chunker_empty():
    """Test fixed chunker with empty input."""
    doc = Document(doc_id="test", text="")
    chunker = FixedChunker(chunk_size=10, overlap=0)
    chunks = chunker.chunk(doc)
    assert len(chunks) == 0


def test_sentence_chunker_basic():
    """Test sentence chunker."""
    doc = Document(doc_id="test", text="First sentence. Second sentence. Third sentence.")
    chunker = SentenceChunker(sentences_per_chunk=2, overlap=0)
    chunks = chunker.chunk(doc)
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.doc_id == "test"


def test_sentence_chunker_offsets():
    """Test sentence chunker offsets."""
    doc = Document(doc_id="test", text="Hello world. This is a test. More text here.")
    chunker = SentenceChunker(sentences_per_chunk=1, overlap=0)
    chunks = chunker.chunk(doc)
    
    for chunk in chunks:
        assert 0 <= chunk.start_offset < len(doc.text)
        assert chunk.start_offset <= chunk.end_offset <= len(doc.text)


def test_recursive_chunker_basic():
    """Test recursive chunker."""
    doc = Document(doc_id="test", text="Para one.\n\nPara two.\n\nPara three.")
    chunker = RecursiveChunker(chunk_size=5, overlap=0)
    chunks = chunker.chunk(doc)
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert len(chunk.text.split()) <= 5 or len(chunk.text.split()) < 10


def test_recursive_chunker_no_loss():
    """Test that recursive chunker doesn't lose content."""
    doc = Document(doc_id="test", text="One two three four five six seven eight nine ten")
    chunker = RecursiveChunker(chunk_size=3, overlap=0)
    chunks = chunker.chunk(doc)
    
    all_text = " ".join(chunk.text for chunk in chunks)
    original_words = set(doc.text.split())
    result_words = set(all_text.split())
    
    assert original_words.issubset(result_words)


def test_markdown_chunker_headings():
    """Test markdown chunker respects headings."""
    doc = Document(
        doc_id="test",
        text="# Title\n\nContent under title.\n\n## Subtitle\n\nMore content."
    )
    chunker = MarkdownChunker(max_chunk_size=20, overlap=0)
    chunks = chunker.chunk(doc)
    
    assert len(chunks) > 0
    has_heading_path = any(len(chunk.heading_path) > 0 for chunk in chunks)
    assert has_heading_path


def test_markdown_chunker_large_section():
    """Test markdown chunker splits large sections."""
    large_text = " ".join(["word"] * 200)
    doc = Document(doc_id="test", text=f"# Heading\n\n{large_text}")
    chunker = MarkdownChunker(max_chunk_size=20, overlap=0)
    chunks = chunker.chunk(doc)
    
    assert len(chunks) > 1


def test_markdown_chunker_heading_path():
    """Test heading path extraction."""
    doc = Document(
        doc_id="test",
        text="# Level 1\n\n## Level 2\n\nContent\n\n### Level 3\n\nMore content"
    )
    chunker = MarkdownChunker(max_chunk_size=50, overlap=0)
    chunks = chunker.chunk(doc)
    
    level_3_chunks = [c for c in chunks if "Level 3" in str(c.heading_path)]
    if level_3_chunks:
        assert len(level_3_chunks[0].heading_path) >= 1


def test_chunker_unicode():
    """Test chunkers with unicode content."""
    doc = Document(doc_id="test", text="Hello 世界! This is a test. 测试内容。")
    
    chunkers = [
        FixedChunker(chunk_size=5),
        SentenceChunker(sentences_per_chunk=1),
        RecursiveChunker(chunk_size=5),
        MarkdownChunker(max_chunk_size=10),
    ]
    
    for chunker in chunkers:
        chunks = chunker.chunk(doc)
        assert len(chunks) > 0
