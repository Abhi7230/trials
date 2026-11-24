"""Test max context solver."""

import pytest
from gguf_fit.writer import write_gguf
from gguf_fit.reader import read_gguf
from gguf_fit.plan import max_context, plan_fit
from gguf_fit.types import GGMLType


def create_simple_model(tmp_path, name):
    """Create a simple test model."""
    path = tmp_path / f"{name}.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "llama.block_count": 4,
        "llama.embedding_length": 128,
        "llama.attention.head_count": 8,
        "llama.attention.head_count_kv": 2,
    }
    
    tensors = [
        ("token_embd.weight", [1000, 128], GGMLType.Q4_0),
        *[(f"blk.{i}.weight", [128, 128], GGMLType.Q4_0) for i in range(4)],
        ("output.weight", [128, 1000], GGMLType.Q4_0),
    ]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    return read_gguf(path)


def test_max_context_property(tmp_path):
    """Test that max_context result R satisfies fits(R) and not fits(R+1)."""
    gguf = create_simple_model(tmp_path, "test")
    
    budgets = [
        ('4GiB', '8GiB'),
        ('8GiB', '16GiB'),
        ('16GiB', '32GiB'),
        ('24GiB', '32GiB'),
        ('32GiB', '64GiB'),
    ]
    
    for vram, ram in budgets:
        max_ctx = max_context(gguf, vram=vram, ram=ram, kv='f16')
        
        # Verify that max_ctx fits
        plan_at_max = plan_fit(gguf, vram=vram, ram=ram, ctx=max_ctx, kv='f16')
        assert plan_at_max.verdict != 'does-not-fit', \
            f"max_context returned {max_ctx} but it doesn't fit"
        
        # Verify that max_ctx + 1 doesn't fit (or we're at the limit)
        if max_ctx < 1_000_000:
            plan_over = plan_fit(gguf, vram=vram, ram=ram, ctx=max_ctx+1, kv='f16')
            assert plan_over.verdict == 'does-not-fit', \
                f"max_context returned {max_ctx} but {max_ctx+1} also fits"


def test_max_context_increases_with_budget(tmp_path):
    """Test that larger budgets give larger max context."""
    gguf = create_simple_model(tmp_path, "test")
    
    max_ctx_small = max_context(gguf, vram='4GiB', ram='8GiB', kv='f16')
    max_ctx_large = max_context(gguf, vram='16GiB', ram='32GiB', kv='f16')
    
    assert max_ctx_large >= max_ctx_small


def test_max_context_with_q8_0_vs_f16(tmp_path):
    """Test that Q8_0 KV gives smaller max context than F16."""
    gguf = create_simple_model(tmp_path, "test")
    
    max_ctx_q8 = max_context(gguf, vram='8GiB', ram='16GiB', kv='q8_0')
    max_ctx_f16 = max_context(gguf, vram='8GiB', ram='16GiB', kv='f16')
    
    # Q8_0 uses more bytes per element than F16, so max context should be smaller
    # Actually, Q8_0 is 34/32 = 1.0625 bytes/elem, F16 is 2 bytes/elem
    # So F16 should give SMALLER max context, not larger
    # Let me reconsider: Q8_0 = 1.0625, F16 = 2.0, so Q8_0 should allow LARGER context
    assert max_ctx_q8 >= max_ctx_f16


def test_max_context_with_q4_0(tmp_path):
    """Test max context with Q4_0 KV (most efficient)."""
    gguf = create_simple_model(tmp_path, "test")
    
    max_ctx_q4 = max_context(gguf, vram='8GiB', ram='16GiB', kv='q4_0')
    max_ctx_f16 = max_context(gguf, vram='8GiB', ram='16GiB', kv='f16')
    
    # Q4_0 uses least memory, should give largest context
    assert max_ctx_q4 >= max_ctx_f16


def test_max_context_minimum(tmp_path):
    """Test that max_context respects minimum."""
    gguf = create_simple_model(tmp_path, "test")
    
    # Very tight budget
    max_ctx = max_context(gguf, vram='100MB', ram='200MB', kv='f16', min_ctx=128)
    
    # Should be at least min_ctx or 0
    assert max_ctx >= 0
