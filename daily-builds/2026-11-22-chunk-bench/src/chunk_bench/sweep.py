"""Sweep over chunking configurations."""

import json
from .models import BenchmarkConfig, BenchmarkResult, Question
from .corpus import load_corpus
from .chunkers import get_chunker
from .retrieve import get_retriever
from .embed import HashEmbedder
from .metrics import calculate_metrics


def run_sweep(
    corpus_dir: str,
    questions: list[Question],
    strategies: list[str],
    sizes: list[int],
    overlaps: list[int],
    retrievers: list[str],
    k: int = 3,
    seed: int = 1,
) -> list[BenchmarkResult]:
    """Run a parameter sweep over configurations."""
    documents = load_corpus(corpus_dir)
    results = []
    
    for strategy in strategies:
        for size in sizes:
            for overlap in overlaps:
                for retriever_type in retrievers:
                    config = BenchmarkConfig(
                        strategy=strategy,
                        size=size,
                        overlap=overlap,
                        retriever=retriever_type,
                        k=k,
                        seed=seed,
                    )
                    
                    chunker = get_chunker(strategy, size, overlap)
                    all_chunks = []
                    for doc in documents:
                        chunks = chunker.chunk(doc)
                        all_chunks.extend(chunks)
                    
                    embedder = HashEmbedder(seed=seed)
                    retriever = get_retriever(retriever_type, embedder)
                    retriever.index(all_chunks)
                    
                    retrieval_results = []
                    for question in questions:
                        result = retriever.retrieve(question.question, k)
                        retrieval_results.append(result)
                    
                    metrics = calculate_metrics(questions, retrieval_results, all_chunks, k)
                    
                    results.append(BenchmarkResult(config=config, metrics=metrics))
    
    return results


def find_best_config(results: list[BenchmarkResult], metric: str = "hit_at_k") -> BenchmarkResult:
    """Find the best configuration by a metric."""
    if not results:
        raise ValueError("No results to compare")
    
    return max(results, key=lambda r: getattr(r.metrics, metric))


def find_pareto_frontier(results: list[BenchmarkResult]) -> list[BenchmarkResult]:
    """Find Pareto optimal configs (quality vs tokens)."""
    pareto = []
    
    for result in results:
        dominated = False
        for other in results:
            if other == result:
                continue
            
            if (other.metrics.hit_at_k >= result.metrics.hit_at_k and
                other.metrics.avg_tokens_retrieved <= result.metrics.avg_tokens_retrieved and
                (other.metrics.hit_at_k > result.metrics.hit_at_k or
                 other.metrics.avg_tokens_retrieved < result.metrics.avg_tokens_retrieved)):
                dominated = True
                break
        
        if not dominated:
            pareto.append(result)
    
    return pareto
