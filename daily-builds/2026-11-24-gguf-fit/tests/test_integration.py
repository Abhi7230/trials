"""End-to-end integration tests."""

import subprocess
import sys
from pathlib import Path


def test_full_workflow(tmp_path):
    """Test complete workflow: create fixture, inspect, fit, compare."""
    # Create fixtures
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'make-fixture', '--out', str(tmp_path), '--preset', 'tiny-llama'],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'make-fixture', '--out', str(tmp_path), '--preset', 'tiny-moe'],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    
    llama_path = tmp_path / 'tiny-llama.gguf'
    moe_path = tmp_path / 'tiny-moe.gguf'
    
    assert llama_path.exists()
    assert moe_path.exists()
    
    # Inspect
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'inspect', str(llama_path), '--format', 'json'],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    
    import json
    data = json.loads(result.stdout)
    assert data['architecture'] == 'llama'
    
    # Fit
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'fit', str(llama_path), '--vram', '8GiB', '--ctx', '8192'],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    
    # Compare
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'compare', str(llama_path), str(moe_path), '--ctx', '8192'],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_json_output_stable(tmp_path):
    """Test that JSON output is stable across two invocations."""
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'make-fixture', '--out', str(tmp_path), '--preset', 'tiny-llama'],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    
    path = tmp_path / 'tiny-llama.gguf'
    
    # Run inspect twice
    result1 = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'inspect', str(path), '--format', 'json'],
        capture_output=True,
        text=True,
    )
    
    result2 = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'inspect', str(path), '--format', 'json'],
        capture_output=True,
        text=True,
    )
    
    assert result1.stdout == result2.stdout


def test_all_output_formats(tmp_path):
    """Test that all output formats work."""
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'make-fixture', '--out', str(tmp_path), '--preset', 'tiny-llama'],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    
    path = tmp_path / 'tiny-llama.gguf'
    
    for fmt in ['text', 'json', 'markdown']:
        result = subprocess.run(
            [sys.executable, '-m', 'gguf_fit.cli', 'inspect', str(path), '--format', fmt],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert len(result.stdout) > 0


def test_library_api(tmp_path):
    """Test library API usage."""
    from gguf_fit import read_gguf, estimate, plan_fit, summarize
    from gguf_fit.writer import write_gguf
    from gguf_fit.types import GGMLType
    
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "llama.block_count": 4,
        "llama.embedding_length": 128,
        "llama.attention.head_count": 8,
        "llama.attention.head_count_kv": 2,
    }
    
    tensors = [
        ("token_embd.weight", [1000, 128], GGMLType.Q4_0),
        ("output.weight", [128, 1000], GGMLType.Q4_0),
    ]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    
    # Read
    m = read_gguf(path)
    assert m.version == 3
    
    # Summarize
    summary = summarize(m)
    assert summary.architecture == "llama"
    
    # Estimate
    est = estimate(m, ctx=32768, kv='q8_0')
    assert est.context_length == 32768
    
    # Plan fit
    plan = plan_fit(m, vram='24GiB', ram='32GiB', ctx=32768, kv='q8_0')
    assert plan.verdict in ('fits-gpu', 'partial-offload', 'cpu-only', 'does-not-fit')


def test_exit_codes(tmp_path):
    """Test that exit codes match spec."""
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'make-fixture', '--out', str(tmp_path), '--preset', 'tiny-llama'],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    
    path = tmp_path / 'tiny-llama.gguf'
    
    # Exit 0: fits
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'fit', str(path), 
         '--vram', '100GiB', '--fail-if-over'],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    
    # Exit 1: doesn't fit
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'fit', str(path), 
         '--vram', '1KB', '--ram', '1KB', '--ctx', '100000', '--fail-if-over'],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    
    # Exit 2: parse/usage error
    result = subprocess.run(
        [sys.executable, '-m', 'gguf_fit.cli', 'inspect', str(tmp_path / 'nonexistent.gguf')],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
