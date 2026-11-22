"""Sentence-based chunker."""

from ..models import Document, Chunk
from ..tokenize import split_by_sentences


class SentenceChunker:
    """Chunk by grouping N sentences."""
    
    def __init__(self, sentences_per_chunk: int, overlap: int = 0):
        self.sentences_per_chunk = sentences_per_chunk
        self.overlap = overlap
    
    def chunk(self, doc: Document) -> list[Chunk]:
        """Chunk document by sentences."""
        sentences = split_by_sentences(doc.text)
        chunks = []
        
        if not sentences:
            return chunks
        
        stride = max(1, self.sentences_per_chunk - self.overlap)
        
        for i in range(0, len(sentences), stride):
            chunk_sentences = sentences[i:i + self.sentences_per_chunk]
            if not chunk_sentences:
                continue
            
            chunk_text = " ".join(chunk_sentences)
            start_offset = doc.text.find(chunk_sentences[0])
            last_sentence = chunk_sentences[-1]
            end_offset = doc.text.find(last_sentence, start_offset) + len(last_sentence)
            
            chunks.append(Chunk(
                doc_id=doc.doc_id,
                text=chunk_text,
                start_offset=max(0, start_offset),
                end_offset=min(len(doc.text), end_offset),
            ))
        
        return chunks
