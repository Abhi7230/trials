"""Command-line interface."""

import sys
from pathlib import Path
from typing import Annotated, Literal

import typer
from rich.console import Console

from . import report
from .compare import compare as compare_fn
from .errors import GGUFError
from .plan import max_context as max_context_fn
from .plan import plan_fit
from .reader import read_gguf
from .summary import summarize
from .writer import write_gguf
from .types import GGMLType

app = typer.Typer(help="GGUF fit analyzer - parse GGUF files and estimate memory")
console = Console()


@app.command()
def inspect(
    model_path: Annotated[Path, typer.Argument(help="Path to GGUF file")],
    tensors: Annotated[bool, typer.Option(help="Show largest tensors")] = False,
    format: Annotated[Literal['text', 'json', 'markdown'], typer.Option(help="Output format")] = 'text',
) -> None:
    """Inspect GGUF model and show summary."""
    try:
        gguf = read_gguf(model_path)
        summary = summarize(gguf, top_tensors=10)
        
        if format == 'text':
            output = report.text.format_summary(summary, show_tensors=tensors)
        elif format == 'json':
            output = report.json.format_summary(summary, show_tensors=tensors)
        elif format == 'markdown':
            output = report.markdown.format_summary(summary, show_tensors=tensors)
        
        console.print(output)
        
    except typer.Exit:
        raise
    except GGUFError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        raise typer.Exit(2)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", style="bold red")
        raise typer.Exit(2)


@app.command()
def fit(
    model_path: Annotated[Path, typer.Argument(help="Path to GGUF file")],
    vram: Annotated[str, typer.Option(help="VRAM budget (e.g. 24GiB)")] = "24GiB",
    ram: Annotated[str, typer.Option(help="RAM budget (e.g. 32GiB)")] = "0",
    ctx: Annotated[int, typer.Option(help="Context length")] = 2048,
    kv: Annotated[str, typer.Option(help="KV cache dtype (f16, q8_0, q4_0)")] = "f16",
    parallel: Annotated[int, typer.Option(help="Number of parallel slots")] = 1,
    fail_if_over: Annotated[bool, typer.Option(help="Exit 1 if doesn't fit")] = False,
    format: Annotated[Literal['text', 'json', 'markdown'], typer.Option(help="Output format")] = 'text',
) -> None:
    """Check if model fits in memory budget."""
    try:
        gguf = read_gguf(model_path)
        plan = plan_fit(gguf, vram=vram, ram=ram, ctx=ctx, kv=kv, parallel=parallel)
        
        if format == 'text':
            output = report.text.format_plan(plan)
        elif format == 'json':
            output = report.json.format_plan(plan)
        elif format == 'markdown':
            output = report.markdown.format_plan(plan)
        
        console.print(output)
        
        if fail_if_over and plan.verdict == 'does-not-fit':
            raise typer.Exit(1)
        
    except typer.Exit:
        raise
    except GGUFError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        raise typer.Exit(2)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", style="bold red")
        raise typer.Exit(2)


@app.command()
def max_ctx(
    model_path: Annotated[Path, typer.Argument(help="Path to GGUF file")],
    vram: Annotated[str, typer.Option(help="VRAM budget (e.g. 24GiB)")] = "24GiB",
    ram: Annotated[str, typer.Option(help="RAM budget (e.g. 32GiB)")] = "0",
    kv: Annotated[str, typer.Option(help="KV cache dtype (f16, q8_0, q4_0)")] = "f16",
    parallel: Annotated[int, typer.Option(help="Number of parallel slots")] = 1,
) -> None:
    """Find maximum context length that fits budget."""
    try:
        gguf = read_gguf(model_path)
        result = max_context_fn(gguf, vram=vram, ram=ram, kv=kv, parallel=parallel)
        
        console.print(f"Maximum context length: {result:,}")
        
    except typer.Exit:
        raise
    except GGUFError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        raise typer.Exit(2)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", style="bold red")
        raise typer.Exit(2)


@app.command()
def compare(
    model_a: Annotated[Path, typer.Argument(help="First GGUF file")],
    model_b: Annotated[Path, typer.Argument(help="Second GGUF file")],
    ctx: Annotated[int, typer.Option(help="Context length")] = 8192,
    kv: Annotated[str, typer.Option(help="KV cache dtype")] = "f16",
    format: Annotated[Literal['text', 'json', 'markdown'], typer.Option(help="Output format")] = 'text',
) -> None:
    """Compare two GGUF models."""
    try:
        comparison = compare_fn(model_a, model_b, ctx=ctx, kv=kv)
        
        if format == 'text':
            output = report.text.format_comparison(comparison)
        elif format == 'json':
            output = report.json.format_comparison(comparison)
        elif format == 'markdown':
            output = report.markdown.format_comparison(comparison)
        
        console.print(output)
        
    except typer.Exit:
        raise
    except GGUFError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        raise typer.Exit(2)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", style="bold red")
        raise typer.Exit(2)


@app.command()
def make_fixture(
    out: Annotated[Path, typer.Option(help="Output directory")] = Path("tests/fixtures"),
    preset: Annotated[str, typer.Option(help="Preset (tiny-llama, tiny-moe)")] = "tiny-llama",
) -> None:
    """Generate test fixture GGUF files."""
    out.mkdir(parents=True, exist_ok=True)
    
    if preset == "tiny-llama":
        # Small Llama-style model
        metadata = {
            "general.architecture": "llama",
            "general.name": "tiny-llama",
            "llama.block_count": 4,
            "llama.embedding_length": 128,
            "llama.attention.head_count": 8,
            "llama.attention.head_count_kv": 2,
            "llama.context_length": 2048,
            "llama.vocab_size": 1000,
        }
        tensors = [
            ("token_embd.weight", [1000, 128], GGMLType.Q4_0),
            *[(f"blk.{i}.attn_q.weight", [128, 128], GGMLType.Q4_0) for i in range(4)],
            *[(f"blk.{i}.attn_k.weight", [128, 32], GGMLType.Q4_0) for i in range(4)],
            *[(f"blk.{i}.attn_v.weight", [128, 32], GGMLType.Q4_0) for i in range(4)],
            *[(f"blk.{i}.attn_output.weight", [128, 128], GGMLType.Q4_0) for i in range(4)],
            *[(f"blk.{i}.ffn_gate.weight", [128, 512], GGMLType.Q4_0) for i in range(4)],
            *[(f"blk.{i}.ffn_up.weight", [128, 512], GGMLType.Q4_0) for i in range(4)],
            *[(f"blk.{i}.ffn_down.weight", [512, 128], GGMLType.Q4_0) for i in range(4)],
            ("output.weight", [128, 1000], GGMLType.Q4_0),
        ]
        path = out / "tiny-llama.gguf"
        
    elif preset == "tiny-moe":
        # Small MoE model
        metadata = {
            "general.architecture": "mixtral",
            "general.name": "tiny-moe",
            "mixtral.block_count": 2,
            "mixtral.embedding_length": 64,
            "mixtral.attention.head_count": 4,
            "mixtral.attention.head_count_kv": 2,
            "mixtral.context_length": 1024,
            "mixtral.expert_count": 4,
            "mixtral.vocab_size": 500,
        }
        tensors = [
            ("token_embd.weight", [500, 64], GGMLType.Q8_0),
            *[(f"blk.{i}.attn_q.weight", [64, 64], GGMLType.Q8_0) for i in range(2)],
            *[(f"blk.{i}.attn_k.weight", [64, 32], GGMLType.Q8_0) for i in range(2)],
            *[(f"blk.{i}.attn_v.weight", [64, 32], GGMLType.Q8_0) for i in range(2)],
            *[(f"blk.{i}.attn_output.weight", [64, 64], GGMLType.Q8_0) for i in range(2)],
            *[(f"blk.{i}.ffn.gate.{j}.weight", [64, 256], GGMLType.Q8_0) for i in range(2) for j in range(4)],
            *[(f"blk.{i}.ffn.up.{j}.weight", [64, 256], GGMLType.Q8_0) for i in range(2) for j in range(4)],
            *[(f"blk.{i}.ffn.down.{j}.weight", [256, 64], GGMLType.Q8_0) for i in range(2) for j in range(4)],
            ("output.weight", [64, 500], GGMLType.Q8_0),
        ]
        path = out / "tiny-moe.gguf"
    else:
        console.print(f"[red]Unknown preset:[/red] {preset}", style="bold red")
        raise typer.Exit(2)
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    console.print(f"[green]Created:[/green] {path}")


if __name__ == "__main__":
    app()
