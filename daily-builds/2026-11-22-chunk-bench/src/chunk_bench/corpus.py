"""Corpus loader for markdown and text files."""

import re
from pathlib import Path
from .models import Document


def strip_frontmatter(text: str) -> str:
    """Strip YAML frontmatter from text."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text


def load_corpus(corpus_dir: str | Path) -> list[Document]:
    """Load all markdown and text files from a directory."""
    corpus_path = Path(corpus_dir)
    documents = []
    
    for file_path in sorted(corpus_path.rglob("*")):
        if file_path.suffix in [".md", ".txt"] and file_path.is_file():
            doc_id = str(file_path.relative_to(corpus_path))
            text = file_path.read_text(encoding="utf-8")
            text = strip_frontmatter(text)
            documents.append(Document(doc_id=doc_id, text=text))
    
    return documents
