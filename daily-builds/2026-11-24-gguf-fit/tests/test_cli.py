"""Test CLI interface."""

import pytest
import subprocess
import sys
from pathlib import Path
from gguf_fit.writer import write_gguf
from gguf_fit.types import GGMLType


def test_cli_make_fixture(tmp_path):
    """Test make-fixture command."""
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'make-fixture', '--out', str(tmp_path), '--preset', 'tiny-llama'],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    assert (tmp_path / 'tiny-llama.gguf').exists()


def test_cli_inspect(tmp_path):
    """Test inspect command."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "general.name": "test-model",
    }
    
    tensors = [("t", [1000], GGMLType.Q4_0)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'inspect', str(path)],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    assert "llama" in result.stdout
    assert "test-model" in result.stdout


def test_cli_inspect_json(tmp_path):
    """Test inspect with JSON output."""
    path = tmp_path / "test.gguf"
    
    metadata = {"general.architecture": "gpt2"}
    tensors = [("t", [100], GGMLType.F16)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'inspect', str(path), '--format', 'json'],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    
    import json
    data = json.loads(result.stdout)
    assert data["architecture"] == "gpt2"


def test_cli_fit(tmp_path):
    """Test fit command."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "llama.block_count": 2,
    }
    
    tensors = [("t", [1000], GGMLType.Q4_0)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'fit', str(path), '--vram', '24GiB', '--ctx', '2048'],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    assert "Verdict" in result.stdout or "verdict" in result.stdout


def test_cli_fit_fail_if_over_pass(tmp_path):
    """Test fit --fail-if-over when model fits."""
    path = tmp_path / "test.gguf"
    
    metadata = {}
    tensors = [("t", [100], GGMLType.Q4_0)]  # Small model
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'fit', str(path), 
         '--vram', '24GiB', '--fail-if-over'],
        capture_output=True,
        text=True,
    )
    
    # Should exit 0 (fits)
    assert result.returncode == 0


def test_cli_fit_fail_if_over_fail(tmp_path):
    """Test fit --fail-if-over when model doesn't fit."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "llama.block_count": 80,
        "llama.embedding_length": 8192,
        "llama.attention.head_count": 64,
        "llama.attention.head_count_kv": 8,
    }
    
    # Very large model that won't fit in 1 GiB
    # 100M params * 4 bytes = 400 MB, but with overhead and large KV cache at 32k ctx it won't fit
    tensors = [("t", [100_000_000], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors, declare_only=True)
    
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'fit', str(path), 
         '--vram', '100MB', '--ram', '100MB', '--ctx', '32768', '--fail-if-over'],
        capture_output=True,
        text=True,
    )
    
    # Should exit 1 (doesn't fit)
    assert result.returncode == 1


def test_cli_max_ctx(tmp_path):
    """Test max-ctx command."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "llama.block_count": 4,
        "llama.embedding_length": 128,
        "llama.attention.head_count": 8,
        "llama.attention.head_count_kv": 2,
    }
    
    tensors = [("t", [1000], GGMLType.Q4_0)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'max-ctx', str(path), '--vram', '8GiB'],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    assert "Maximum context" in result.stdout


def test_cli_compare(tmp_path):
    """Test compare command."""
    path_a = tmp_path / "a.gguf"
    path_b = tmp_path / "b.gguf"
    
    metadata = {}
    tensors_a = [("t", [1000], GGMLType.Q4_0)]
    tensors_b = [("t", [1000], GGMLType.Q8_0)]
    
    write_gguf(path_a, version=3, metadata=metadata, tensors=tensors_a)
    write_gguf(path_b, version=3, metadata=metadata, tensors=tensors_b)
    
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'compare', str(path_a), str(path_b)],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    assert "Comparison" in result.stdout or "comparison" in result.stdout.lower()


def test_cli_invalid_file(tmp_path):
    """Test CLI with invalid file."""
    path = tmp_path / "nonexistent.gguf"
    
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'inspect', str(path)],
        capture_output=True,
        text=True,
    )
    
    # Should exit with error code
    assert result.returncode != 0


def test_cli_corrupt_file(tmp_path):
    """Test CLI with corrupt file."""
    path = tmp_path / "corrupt.gguf"
    path.write_bytes(b'BAAD' + b'\x00' * 100)
    
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'inspect', str(path)],
        capture_output=True,
        text=True,
    )
    
    # Should exit 2 (parse error)
    assert result.returncode == 2
    assert "Error" in result.stderr or "Error" in result.stdout
