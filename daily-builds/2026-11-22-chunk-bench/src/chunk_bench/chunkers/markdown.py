"""Markdown-aware chunker that respects heading structure."""

import re
from ..models import Document, Chunk
from ..tokenize import count_tokens


class MarkdownChunker:
    """Chunk markdown by heading structure."""
    
    def __init__(self, max_chunk_size: int, overlap: int = 0):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.min_section_size = 10
    
    def chunk(self, doc: Document) -> list[Chunk]:
        """Chunk markdown document by headings."""
        sections = self._parse_sections(doc.text)
        chunks = []
        
        for section in sections:
            text = section["text"]
            heading_path = section["heading_path"]
            start_offset = section["start_offset"]
            
            if count_tokens(text) <= self.max_chunk_size:
                if text.strip():
                    chunks.append(Chunk(
                        doc_id=doc.doc_id,
                        text=text,
                        start_offset=start_offset,
                        end_offset=start_offset + len(text),
                        heading_path=heading_path,
                    ))
            else:
                sub_chunks = self._split_large_section(text, start_offset)
                for sub_text, sub_start in sub_chunks:
                    chunks.append(Chunk(
                        doc_id=doc.doc_id,
                        text=sub_text,
                        start_offset=sub_start,
                        end_offset=sub_start + len(sub_text),
                        heading_path=heading_path,
                    ))
        
        chunks = self._merge_tiny_sections(chunks)
        return chunks
    
    def _parse_sections(self, text: str) -> list[dict]:
        """Parse markdown into sections by headings."""
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        lines = text.split("\n")
        sections = []
        current_section = {"text": "", "heading_path": [], "start_offset": 0}
        heading_stack = []
        offset = 0
        
        for line in lines:
            match = re.match(heading_pattern, line)
            if match:
                if current_section["text"].strip():
                    sections.append(current_section)
                
                level = len(match.group(1))
                heading = match.group(2).strip()
                
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                
                heading_stack.append((level, heading))
                heading_path = [h[1] for h in heading_stack]
                
                current_section = {
                    "text": line + "\n",
                    "heading_path": heading_path,
                    "start_offset": offset,
                }
            else:
                current_section["text"] += line + "\n"
            
            offset += len(line) + 1
        
        if current_section["text"].strip():
            sections.append(current_section)
        
        return sections
    
    def _split_large_section(self, text: str, start_offset: int) -> list[tuple[str, int]]:
        """Split a large section into smaller chunks."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        current_start = start_offset
        current_offset = start_offset
        
        for para in paragraphs:
            if not para.strip():
                current_offset += len(para) + 2
                continue
            
            if count_tokens(current_chunk + para) > self.max_chunk_size and current_chunk:
                chunks.append((current_chunk.strip(), current_start))
                current_chunk = para + "\n\n"
                current_start = current_offset
            else:
                current_chunk += para + "\n\n"
            
            current_offset += len(para) + 2
        
        if current_chunk.strip():
            chunks.append((current_chunk.strip(), current_start))
        
        return chunks if chunks else [(text, start_offset)]
    
    def _merge_tiny_sections(self, chunks: list[Chunk]) -> list[Chunk]:
        """Merge very small consecutive sections."""
        if not chunks:
            return chunks
        
        merged = []
        current = chunks[0]
        
        for next_chunk in chunks[1:]:
            if (count_tokens(current.text) < self.min_section_size and
                count_tokens(current.text + next_chunk.text) <= self.max_chunk_size and
                current.doc_id == next_chunk.doc_id):
                current = Chunk(
                    doc_id=current.doc_id,
                    text=current.text + " " + next_chunk.text,
                    start_offset=current.start_offset,
                    end_offset=next_chunk.end_offset,
                    heading_path=current.heading_path,
                )
            else:
                merged.append(current)
                current = next_chunk
        
        merged.append(current)
        return merged
