"""Recursive text splitter."""

from ..models import Document, Chunk
from ..tokenize import count_tokens


class RecursiveChunker:
    """Recursively split by separators until chunks are small enough."""
    
    def __init__(self, chunk_size: int, overlap: int = 0):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separators = ["\n\n", "\n", ". ", " "]
    
    def chunk(self, doc: Document) -> list[Chunk]:
        """Chunk document recursively."""
        splits = self._split_text(doc.text, 0)
        chunks = []
        
        for text, start_offset in splits:
            if not text.strip():
                continue
            chunks.append(Chunk(
                doc_id=doc.doc_id,
                text=text,
                start_offset=start_offset,
                end_offset=start_offset + len(text),
            ))
        
        return chunks
    
    def _split_text(self, text: str, offset: int) -> list[tuple[str, int]]:
        """Split text recursively."""
        if count_tokens(text) <= self.chunk_size:
            return [(text, offset)] if text.strip() else []
        
        for separator in self.separators:
            if separator in text:
                parts = text.split(separator)
                result = []
                current_offset = offset
                
                for i, part in enumerate(parts):
                    if i > 0:
                        current_offset += len(separator)
                    
                    if count_tokens(part) > self.chunk_size:
                        result.extend(self._split_text(part, current_offset))
                    elif part.strip():
                        result.append((part, current_offset))
                    
                    current_offset += len(part)
                
                return result
        
        tokens = text.split()
        if len(tokens) > self.chunk_size:
            mid = len(tokens) // 2
            left = " ".join(tokens[:mid])
            right = " ".join(tokens[mid:])
            result = self._split_text(left, offset)
            result.extend(self._split_text(right, offset + len(left) + 1))
            return result
        
        return [(text, offset)] if text.strip() else []
