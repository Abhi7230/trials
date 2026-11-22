"""Tests for CLI."""

import pytest
import tempfile
import json
from pathlib import Path
from typer.testing import CliRunner
from chunk_bench.cli import app

runner = CliRunner()


def test_cli_strategies():
    """Test strategies command."""
    result = runner.invoke(app, ["strategies"])
    
    assert result.exit_code == 0
    assert "fixed" in result.stdout
    assert "markdown" in result.stdout


def test_cli_synth(tmp_path):
    """Test synth command."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    
    (corpus_dir / "test.md").write_text("First sentence. Second sentence. Third sentence.")
    
    out_file = tmp_path / "questions.jsonl"
    
    result = runner.invoke(app, [
        "synth",
        "--corpus", str(corpus_dir),
        "--out", str(out_file),
        "--n", "3",
        "--seed", "1"
    ])
    
    assert result.exit_code == 0
    assert out_file.exists()
    
    lines = out_file.read_text().strip().split("\n")
    assert len(lines) > 0


def test_cli_chunk(tmp_path):
    """Test chunk command."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Title\n\nSome content here.")
    
    result = runner.invoke(app, [
        "chunk",
        str(test_file),
        "--strategy", "markdown",
        "--size", "10"
    ])
    
    assert result.exit_code == 0
    assert "Chunk" in result.stdout
