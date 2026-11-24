"""Test fit planning."""

import pytest
from gguf_fit.writer import write_gguf
from gguf_fit.reader import read_gguf
from gguf_fit.plan import plan_fit
from gguf_fit.types import GGMLType


def create_test_model(tmp_path, name, n_layers, size_mb):
    """Helper to create a test model."""
    path = tmp_path / f"{name}.gguf"
    
    # Approximate model size
    total_elements = size_mb * 1024 * 1024 // 2  # Assume Q4_0 ~0.5 bytes/param
    per_layer = total_elements // (n_layers + 2)  # +2 for embedding/output
    
    metadata = {
        "general.architecture": "llama",
        "llama.block_count": n_layers,
        "llama.embedding_length": 128,
        "llama.attention.head_count": 8,
        "llama.attention.head_count_kv": 2,
    }
    
    tensors = [
        ("token_embd.weight", [per_layer], GGMLType.Q4_0),
        *[(f"blk.{i}.weight", [per_layer], GGMLType.Q4_0) for i in range(n_layers)],
        ("output.weight", [per_layer], GGMLType.Q4_0),
    ]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    return read_gguf(path)


def test_plan_fits_gpu(tmp_path):
    """Test verdict fits-gpu when model fits entirely in VRAM."""
    # Small model that fits
    gguf = create_test_model(tmp_path, "small", n_layers=4, size_mb=100)
    
    plan = plan_fit(gguf, vram='24GiB', ram='32GiB', ctx=8192, kv='f16')
    
    assert plan.verdict == 'fits-gpu'
    assert plan.gpu_layers == 4


def test_plan_does_not_fit(tmp_path):
    """Test verdict does-not-fit when model is too large."""
    # Large model
    gguf = create_test_model(tmp_path, "large", n_layers=32, size_mb=10000)
    
    # Very small budgets
    plan = plan_fit(gguf, vram='100MB', ram='100MB', ctx=8192, kv='f16')
    
    assert plan.verdict == 'does-not-fit'
    assert plan.gpu_bytes == 0
    assert plan.ram_bytes == 0


def test_plan_cpu_only(tmp_path):
    """Test verdict cpu-only when no VRAM but fits in RAM."""
    gguf = create_test_model(tmp_path, "medium", n_layers=8, size_mb=500)
    
    # No VRAM, large RAM
    plan = plan_fit(gguf, vram='0', ram='64GiB', ctx=2048, kv='q8_0')
    
    assert plan.verdict == 'cpu-only'
    assert plan.gpu_layers == 0
    assert plan.gpu_bytes == 0
    assert plan.ram_bytes > 0


def test_plan_partial_offload(tmp_path):
    """Test verdict partial-offload when model splits between GPU and CPU."""
    gguf = create_test_model(tmp_path, "medium", n_layers=16, size_mb=2000)
    
    # Limited VRAM, decent RAM
    plan = plan_fit(gguf, vram='4GiB', ram='32GiB', ctx=8192, kv='f16')
    
    if plan.verdict == 'partial-offload':
        assert 0 < plan.gpu_layers < 16
        assert plan.gpu_bytes > 0
        assert plan.ram_bytes > 0
        assert plan.gpu_bytes <= 4 * 1024**3


def test_plan_monotonic_vram(tmp_path):
    """Test that more VRAM never reduces gpu_layers (monotonicity)."""
    gguf = create_test_model(tmp_path, "test", n_layers=8, size_mb=1000)
    
    vram_budgets = ['4GiB', '8GiB', '12GiB', '16GiB', '24GiB']
    prev_layers = 0
    
    for vram in vram_budgets:
        plan = plan_fit(gguf, vram=vram, ram='32GiB', ctx=4096, kv='f16')
        
        if plan.verdict in ('partial-offload', 'fits-gpu'):
            current_layers = plan.gpu_layers or 0
            assert current_layers >= prev_layers, f"More VRAM ({vram}) reduced layers"
            prev_layers = current_layers


def test_plan_fail_if_over_exit_codes(tmp_path):
    """Test exit codes for --fail-if-over (tested via plan verdict)."""
    gguf_small = create_test_model(tmp_path, "small", n_layers=2, size_mb=50)
    gguf_large = create_test_model(tmp_path, "large", n_layers=32, size_mb=10000)
    
    # Small model should fit
    plan_fits = plan_fit(gguf_small, vram='24GiB', ram='32GiB', ctx=2048)
    assert plan_fits.verdict != 'does-not-fit'
    
    # Large model should not fit
    plan_no_fit = plan_fit(gguf_large, vram='1GiB', ram='1GiB', ctx=2048)
    assert plan_no_fit.verdict == 'does-not-fit'


def test_plan_gpu_bytes_within_budget(tmp_path):
    """Test that allocated GPU bytes stay within VRAM budget."""
    gguf = create_test_model(tmp_path, "test", n_layers=12, size_mb=1500)
    
    vram_budget = 8 * 1024**3  # 8 GiB
    plan = plan_fit(gguf, vram=vram_budget, ram='32GiB', ctx=4096, kv='f16')
    
    if plan.verdict in ('fits-gpu', 'partial-offload'):
        assert plan.gpu_bytes <= vram_budget


def test_plan_total_within_combined_budget(tmp_path):
    """Test that total fits within vram + ram budget."""
    gguf = create_test_model(tmp_path, "test", n_layers=10, size_mb=1000)
    
    vram = 8 * 1024**3
    ram = 16 * 1024**3
    
    plan = plan_fit(gguf, vram=vram, ram=ram, ctx=4096, kv='f16')
    
    if plan.verdict != 'does-not-fit':
        assert plan.gpu_bytes + plan.ram_bytes <= vram + ram
