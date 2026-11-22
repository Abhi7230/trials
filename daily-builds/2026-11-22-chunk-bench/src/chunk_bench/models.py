"""Data models for chunk benchmark."""

from typing import Any, Protocol
from pydantic import BaseModel, Field, ConfigDict
import numpy as np


class Chunk(BaseModel):
    """A chunk of text with metadata."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    doc_id: str
    text: str
    start_offset: int
    end_offset: int
    heading_path: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """A document with an id and content."""
    
    doc_id: str
    text: str


class Question(BaseModel):
    """An evaluation question with ground truth."""
    
    question: str
    gold_doc: str
    gold_substring: str | None = None
    gold_start: int | None = None
    gold_end: int | None = None


class RetrievalResult(BaseModel):
    """Results from retrieval."""
    
    chunks: list[Chunk]
    scores: list[float]


class MetricResults(BaseModel):
    """Evaluation metrics for a configuration."""
    
    hit_at_k: float
    mrr: float
    recall_at_k: float
    context_precision: float
    avg_tokens_retrieved: float
    chunk_count: int
    index_size_bytes: int
    redundancy: float


class BenchmarkConfig(BaseModel):
    """Configuration for a benchmark run."""
    
    strategy: str
    size: int
    overlap: int
    retriever: str
    k: int = 3
    seed: int = 1


class BenchmarkResult(BaseModel):
    """Results from a benchmark sweep."""
    
    config: BenchmarkConfig
    metrics: MetricResults


class Chunker(Protocol):
    """Protocol for chunking strategies."""
    
    def chunk(self, doc: Document) -> list[Chunk]:
        """Chunk a document into smaller pieces."""
        ...


class Embedder(Protocol):
    """Protocol for embedding text."""
    
    def embed(self, text: str) -> np.ndarray:
        """Embed text to a vector."""
        ...
    
    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts."""
        ...


class Retriever(Protocol):
    """Protocol for retrieving chunks."""
    
    def index(self, chunks: list[Chunk]) -> None:
        """Index chunks for retrieval."""
        ...
    
    def retrieve(self, query: str, k: int) -> RetrievalResult:
        """Retrieve top-k chunks for a query."""
        ...
