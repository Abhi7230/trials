"""Fixed-size chunker with overlap."""

from ..models import Document, Chunk
from ..tokenize import tokenize


class FixedChunker:
    """Chunk by fixed token size with overlap."""
    
    def __init__(self, chunk_size: int, overlap: int = 0):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, doc: Document) -> list[Chunk]:
        """Chunk document into fixed-size pieces."""
        tokens = tokenize(doc.text)
        chunks = []
        
        if not tokens:
            return chunks
        
        stride = max(1, self.chunk_size - self.overlap)
        
        for i in range(0, len(tokens), stride):
            chunk_tokens = tokens[i:i + self.chunk_size]
            if not chunk_tokens:
                continue
            
            chunk_text = " ".join(chunk_tokens)
            start_offset = self._find_offset(doc.text, tokens, i)
            end_offset = self._find_offset(doc.text, tokens, i + len(chunk_tokens))
            
            chunks.append(Chunk(
                doc_id=doc.doc_id,
                text=chunk_text,
                start_offset=start_offset,
                end_offset=end_offset,
            ))
        
        return chunks
    
    def _find_offset(self, text: str, tokens: list[str], token_idx: int) -> int:
        """Find character offset for a token index."""
        if token_idx >= len(tokens):
            return len(text)
        if token_idx == 0:
            return 0
        
        search_text = " ".join(tokens[:token_idx])
        offset = len(search_text)
        if offset < len(text) and text[offset] == " ":
            offset += 1
        return min(offset, len(text))
