"""Evaluation metrics for chunking strategies."""

import sys
from .models import Chunk, Question, MetricResults, RetrievalResult
from .tokenize import count_tokens


def is_relevant(chunk: Chunk, question: Question) -> bool:
    """Check if a chunk is relevant to a question."""
    if question.gold_substring:
        return question.gold_substring in chunk.text
    
    if question.gold_start is not None and question.gold_end is not None:
        chunk_start = chunk.start_offset
        chunk_end = chunk.end_offset
        
        return not (chunk_end <= question.gold_start or chunk_start >= question.gold_end)
    
    return chunk.doc_id == question.gold_doc


def calculate_metrics(
    questions: list[Question],
    retrieval_results: list[RetrievalResult],
    all_chunks: list[Chunk],
    k: int = 3
) -> MetricResults:
    """Calculate evaluation metrics."""
    if len(questions) != len(retrieval_results):
        raise ValueError("Mismatch between questions and results")
    
    hits = 0
    reciprocal_ranks = []
    recalls = []
    total_tokens = 0
    relevant_in_top_k = 0
    
    for question, result in zip(questions, retrieval_results):
        found = False
        rank = None
        relevant_count = 0
        
        for idx, chunk in enumerate(result.chunks[:k]):
            if is_relevant(chunk, question):
                if not found:
                    found = True
                    rank = idx + 1
                relevant_count += 1
        
        if found:
            hits += 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)
        
        recalls.append(1.0 if found else 0.0)
        
        if relevant_count > 0:
            relevant_in_top_k += relevant_count
        
        for chunk in result.chunks[:k]:
            total_tokens += count_tokens(chunk.text)
    
    hit_at_k = hits / len(questions) if questions else 0.0
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
    recall_at_k = sum(recalls) / len(recalls) if recalls else 0.0
    avg_tokens = total_tokens / len(questions) if questions else 0.0
    
    total_retrieved = sum(len(r.chunks[:k]) for r in retrieval_results)
    context_precision = relevant_in_top_k / total_retrieved if total_retrieved > 0 else 0.0
    
    chunk_count = len(all_chunks)
    index_size = sum(len(chunk.text.encode('utf-8')) for chunk in all_chunks)
    
    redundancy = calculate_redundancy(all_chunks)
    
    return MetricResults(
        hit_at_k=hit_at_k,
        mrr=mrr,
        recall_at_k=recall_at_k,
        context_precision=context_precision,
        avg_tokens_retrieved=avg_tokens,
        chunk_count=chunk_count,
        index_size_bytes=index_size,
        redundancy=redundancy,
    )


def calculate_redundancy(chunks: list[Chunk]) -> float:
    """Calculate overlap redundancy ratio."""
    if len(chunks) <= 1:
        return 0.0
    
    chunks_by_doc = {}
    for chunk in chunks:
        if chunk.doc_id not in chunks_by_doc:
            chunks_by_doc[chunk.doc_id] = []
        chunks_by_doc[chunk.doc_id].append(chunk)
    
    total_overlap = 0
    total_length = 0
    
    for doc_chunks in chunks_by_doc.values():
        sorted_chunks = sorted(doc_chunks, key=lambda c: c.start_offset)
        for i in range(len(sorted_chunks) - 1):
            curr = sorted_chunks[i]
            next_chunk = sorted_chunks[i + 1]
            
            if curr.end_offset > next_chunk.start_offset:
                overlap = curr.end_offset - next_chunk.start_offset
                total_overlap += overlap
        
        total_length += sum(len(c.text) for c in sorted_chunks)
    
    return total_overlap / total_length if total_length > 0 else 0.0
