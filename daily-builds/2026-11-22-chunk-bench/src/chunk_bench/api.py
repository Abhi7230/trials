"""FastAPI service for chunk benchmarking."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from .models import Question, BenchmarkConfig, BenchmarkResult, Document
from .chunkers import get_chunker
from .retrieve import get_retriever
from .embed import HashEmbedder
from .metrics import calculate_metrics


app = FastAPI(title="Chunk Bench API")


class EvaluateRequest(BaseModel):
    """Request for evaluation."""
    texts: List[dict]
    questions: List[dict]
    config: dict


class StrategyInfo(BaseModel):
    """Information about a chunking strategy."""
    name: str
    description: str
    parameters: List[str]


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Chunk Bench API", "version": "0.1.0"}


@app.get("/strategies", response_model=List[StrategyInfo])
def list_strategies():
    """List available chunking strategies."""
    return [
        StrategyInfo(
            name="fixed",
            description="Fixed-size chunks with token overlap",
            parameters=["size", "overlap"],
        ),
        StrategyInfo(
            name="sentence",
            description="Group N sentences per chunk",
            parameters=["size", "overlap"],
        ),
        StrategyInfo(
            name="recursive",
            description="Recursive splitting by separators",
            parameters=["size", "overlap"],
        ),
        StrategyInfo(
            name="markdown",
            description="Markdown-aware heading-based chunks",
            parameters=["size", "overlap"],
        ),
    ]


@app.post("/evaluate")
def evaluate(request: EvaluateRequest):
    """Evaluate a chunking configuration."""
    try:
        documents = [Document(**doc) for doc in request.texts]
        questions = [Question(**q) for q in request.questions]
        config = BenchmarkConfig(**request.config)
        
        chunker = get_chunker(config.strategy, config.size, config.overlap)
        all_chunks = []
        for doc in documents:
            chunks = chunker.chunk(doc)
            all_chunks.extend(chunks)
        
        embedder = HashEmbedder(seed=config.seed)
        retriever = get_retriever(config.retriever, embedder)
        retriever.index(all_chunks)
        
        retrieval_results = []
        for question in questions:
            result = retriever.retrieve(question.question, config.k)
            retrieval_results.append(result)
        
        metrics = calculate_metrics(questions, retrieval_results, all_chunks, config.k)
        
        result = BenchmarkResult(config=config, metrics=metrics)
        return result.model_dump()
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
