"""Command-line interface for chunk-bench."""

import sys
import json
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
import uvicorn

from .models import Question, Document
from .corpus import load_corpus
from .chunkers import get_chunker
from .sweep import run_sweep, find_best_config
from .compare import compare_to_baseline, save_baseline
from .synth import generate_questions
from .report import format_table, format_json, format_markdown

app = typer.Typer(help="Offline RAG chunking benchmark")
console = Console()


@app.command()
def run(
    corpus: str = typer.Option(..., help="Corpus directory"),
    questions: str = typer.Option(..., help="Questions file (JSONL or YAML)"),
    strategy: str = typer.Option("fixed,sentence,recursive,markdown", help="Comma-separated strategies"),
    size: str = typer.Option("64,128,256", help="Comma-separated chunk sizes"),
    overlap: str = typer.Option("0,16", help="Comma-separated overlap values"),
    retriever: str = typer.Option("dense,bm25,hybrid", help="Comma-separated retrievers"),
    k: int = typer.Option(3, help="Top-k for retrieval"),
    seed: int = typer.Option(1, help="Random seed"),
    format: str = typer.Option("table", help="Output format: table|json|markdown|csv"),
    min_hit_at_k: Optional[float] = typer.Option(None, help="Minimum hit@k threshold"),
    compare: Optional[str] = typer.Option(None, help="Baseline JSON for comparison"),
    out: Optional[str] = typer.Option(None, help="Output file"),
):
    """Run chunking benchmark sweep."""
    questions_list = load_questions(questions)
    
    strategies = [s.strip() for s in strategy.split(",")]
    sizes = [int(s.strip()) for s in size.split(",")]
    overlaps = [int(o.strip()) for o in overlap.split(",")]
    retrievers = [r.strip() for r in retriever.split(",")]
    
    results = run_sweep(
        corpus_dir=corpus,
        questions=questions_list,
        strategies=strategies,
        sizes=sizes,
        overlaps=overlaps,
        retrievers=retrievers,
        k=k,
        seed=seed,
    )
    
    if format == "table":
        format_table(results)
    elif format == "json":
        output = format_json(results)
        if out:
            Path(out).write_text(output)
        else:
            console.print(output)
    elif format == "markdown":
        output = format_markdown(results)
        if out:
            Path(out).write_text(output)
        else:
            console.print(output)
    
    best = find_best_config(results)
    
    if min_hit_at_k is not None:
        if best.metrics.hit_at_k < min_hit_at_k:
            console.print(f"[red]FAIL: Best hit@{k} = {best.metrics.hit_at_k:.3f} < {min_hit_at_k}[/red]")
            sys.exit(1)
        else:
            console.print(f"[green]PASS: Best hit@{k} = {best.metrics.hit_at_k:.3f} >= {min_hit_at_k}[/green]")
    
    if compare:
        baseline = json.loads(Path(compare).read_text())
        passed, message = compare_to_baseline(best, baseline)
        if not passed:
            console.print(f"[red]{message}[/red]")
            sys.exit(1)
        else:
            console.print(f"[green]{message}[/green]")


@app.command()
def chunk(
    file: str = typer.Argument(..., help="File to chunk"),
    strategy: str = typer.Option("markdown", help="Chunking strategy"),
    size: int = typer.Option(128, help="Chunk size"),
    overlap: int = typer.Option(0, help="Overlap size"),
):
    """Chunk a single file."""
    text = Path(file).read_text()
    doc = Document(doc_id=file, text=text)
    
    chunker = get_chunker(strategy, size, overlap)
    chunks = chunker.chunk(doc)
    
    for i, chunk in enumerate(chunks):
        console.print(f"\n[cyan]Chunk {i+1}[/cyan] ({chunk.start_offset}-{chunk.end_offset})")
        if chunk.heading_path:
            console.print(f"[dim]Headings: {' > '.join(chunk.heading_path)}[/dim]")
        console.print(chunk.text[:200] + ("..." if len(chunk.text) > 200 else ""))


@app.command()
def synth(
    corpus: str = typer.Option(..., help="Corpus directory"),
    out: str = typer.Option("questions.jsonl", help="Output file"),
    n: int = typer.Option(30, help="Number of questions"),
    seed: int = typer.Option(1, help="Random seed"),
):
    """Generate synthetic evaluation questions."""
    documents = load_corpus(corpus)
    questions = generate_questions(documents, n=n, seed=seed)
    
    with open(out, 'w') as f:
        for q in questions:
            f.write(q.model_dump_json() + "\n")
    
    console.print(f"[green]Generated {len(questions)} questions to {out}[/green]")


@app.command()
def strategies():
    """List available chunking strategies."""
    console.print("[cyan]Available Strategies:[/cyan]\n")
    console.print("  [bold]fixed[/bold]: Fixed-size chunks with token overlap")
    console.print("  [bold]sentence[/bold]: Group N sentences per chunk")
    console.print("  [bold]recursive[/bold]: Recursive splitting by separators")
    console.print("  [bold]markdown[/bold]: Markdown-aware heading-based chunks")


@app.command()
def serve(
    port: int = typer.Option(8000, help="Port to listen on"),
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
):
    """Start FastAPI server."""
    from .api import app as fastapi_app
    uvicorn.run(fastapi_app, host=host, port=port)


def load_questions(path: str) -> list[Question]:
    """Load questions from JSONL or YAML file."""
    questions = []
    content = Path(path).read_text()
    
    if path.endswith(".jsonl"):
        for line in content.strip().split("\n"):
            if line.strip():
                questions.append(Question(**json.loads(line)))
    elif path.endswith(".json"):
        data = json.loads(content)
        if isinstance(data, list):
            questions = [Question(**q) for q in data]
        else:
            questions = [Question(**data)]
    else:
        import yaml
        data = yaml.safe_load(content)
        if isinstance(data, list):
            questions = [Question(**q) for q in data]
        else:
            questions = [Question(**data)]
    
    return questions


if __name__ == "__main__":
    app()
