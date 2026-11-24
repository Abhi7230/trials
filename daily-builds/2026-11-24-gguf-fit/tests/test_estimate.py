"""Test memory estimation with exact numbers."""

import pytest
from gguf_fit.writer import write_gguf
from gguf_fit.reader import read_gguf
from gguf_fit.estimate import estimate
from gguf_fit.types import GGMLType


def test_estimate_exact_llama_f16():
    """Test exact KV cache size for Llama-style model with F16.
    
    Spec: 32 layers, 32 heads, 8 KV heads, head_dim 128, ctx 32768
    KV f16 = 2 * 32 * 32768 * 8 * 128 * 2 = 4,294,967,296 bytes (4.00 GiB)
    """
    n_layers = 32
    n_heads = 32
    n_kv_heads = 8
    embedding_length = 32 * 128  # 32 heads * 128 head_dim = 4096
    head_dim = embedding_length // n_heads
    ctx = 32768
    
    # Verify head_dim calculation
    assert head_dim == 128
    
    # Manual calculation
    expected_kv_f16 = 2 * n_layers * ctx * n_kv_heads * head_dim * 2
    assert expected_kv_f16 == 4_294_967_296
    
    # Create synthetic model (tmp_path not needed, use declare_only)
    from pathlib import Path
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "llama.gguf"
        
        metadata = {
            "general.architecture": "llama",
            "llama.block_count": n_layers,
            "llama.embedding_length": embedding_length,
            "llama.attention.head_count": n_heads,
            "llama.attention.head_count_kv": n_kv_heads,
            "llama.context_length": ctx,
        }
        
        # Minimal tensors
        tensors = [("dummy", [1], GGMLType.F32)]
        
        write_gguf(path, version=3, metadata=metadata, tensors=tensors)
        gguf = read_gguf(path)
        est = estimate(gguf, ctx=ctx, kv='f16')
        
        assert est.kv_cache_bytes == 4_294_967_296


def test_estimate_exact_llama_q8_0():
    """Test exact KV cache size for Llama-style model with Q8_0.
    
    Q8_0 has 34 bytes per 32 elements = 1.0625 bytes per element
    KV = 2 (key+value) * 32 layers * 32768 ctx * 8 kv_heads * 128 head_dim * 1.0625
    """
    n_layers = 32
    n_heads = 32
    n_kv_heads = 8
    embedding_length = 4096
    ctx = 32768
    
    head_dim = embedding_length // n_heads
    
    # Manual calculation
    bytes_per_elem = 34 / 32
    expected_kv_q8_0 = int(2 * n_layers * ctx * n_kv_heads * head_dim * bytes_per_elem)
    # This equals 2,281,701,376 bytes (2.125 GiB)
    
    from pathlib import Path
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "llama.gguf"
        
        metadata = {
            "general.architecture": "llama",
            "llama.block_count": n_layers,
            "llama.embedding_length": embedding_length,
            "llama.attention.head_count": n_heads,
            "llama.attention.head_count_kv": n_kv_heads,
        }
        
        tensors = [("dummy", [1], GGMLType.F32)]
        
        write_gguf(path, version=3, metadata=metadata, tensors=tensors)
        gguf = read_gguf(path)
        est = estimate(gguf, ctx=ctx, kv='q8_0')
        
        assert est.kv_cache_bytes == expected_kv_q8_0


def test_estimate_exact_llama_q4_0():
    """Test exact KV cache size for Llama-style model with Q4_0.
    
    Q4_0 has 18 bytes per 32 elements = 0.5625 bytes per element
    KV = 2 * 32 * 32768 * 8 * 128 * 0.5625
    """
    n_layers = 32
    n_heads = 32
    n_kv_heads = 8
    embedding_length = 4096
    ctx = 32768
    
    head_dim = embedding_length // n_heads
    bytes_per_elem = 18 / 32
    expected_kv_q4_0 = int(2 * n_layers * ctx * n_kv_heads * head_dim * bytes_per_elem)
    # This equals 1,207,959,552 bytes (1.125 GiB)
    
    from pathlib import Path
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "llama.gguf"
        
        metadata = {
            "general.architecture": "llama",
            "llama.block_count": n_layers,
            "llama.embedding_length": embedding_length,
            "llama.attention.head_count": n_heads,
            "llama.attention.head_count_kv": n_kv_heads,
        }
        
        tensors = [("dummy", [1], GGMLType.F32)]
        
        write_gguf(path, version=3, metadata=metadata, tensors=tensors)
        gguf = read_gguf(path)
        est = estimate(gguf, ctx=ctx, kv='q4_0')
        
        assert est.kv_cache_bytes == expected_kv_q4_0


def test_estimate_parallel_doubles_kv(tmp_path):
    """Test that parallel=2 doubles KV cache."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "llama.block_count": 2,
        "llama.embedding_length": 128,
        "llama.attention.head_count": 4,
        "llama.attention.head_count_kv": 2,
    }
    
    tensors = [("dummy", [1], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    est1 = estimate(gguf, ctx=1024, kv='f16', parallel=1)
    est2 = estimate(gguf, ctx=1024, kv='f16', parallel=2)
    
    assert est2.kv_cache_bytes == est1.kv_cache_bytes * 2


def test_estimate_sliding_window_reduces_kv(tmp_path):
    """Test that sliding window reduces KV cache size."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "llama.block_count": 4,
        "llama.embedding_length": 128,
        "llama.attention.head_count": 4,
        "llama.attention.head_count_kv": 2,
        "llama.attention.sliding_window": 1024,
    }
    
    tensors = [("dummy", [1], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    # With sliding window, effective ctx is min(ctx, window)
    est_large = estimate(gguf, ctx=8192, kv='f16')
    est_window = estimate(gguf, ctx=1024, kv='f16')
    
    # Both should have same KV cache size (capped at window)
    assert est_large.kv_cache_bytes == est_window.kv_cache_bytes


def test_estimate_weights_overhead(tmp_path):
    """Test that overhead is calculated correctly."""
    path = tmp_path / "test.gguf"
    
    metadata = {}
    # 1000 elements * 4 bytes = 4000 bytes
    tensors = [("t1", [1000], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    est = estimate(gguf, ctx=0)  # No KV cache
    
    # Weights should be 4000 bytes
    assert est.weights_bytes == 4000
    
    # Overhead should be 5% of weights + 256 MiB
    expected_overhead = int(4000 * 0.05) + 256 * 1024 * 1024
    assert est.overhead_bytes == expected_overhead
    
    # Total = weights + KV + overhead
    assert est.total_bytes == est.weights_bytes + est.kv_cache_bytes + est.overhead_bytes


def test_estimate_zero_layers(tmp_path):
    """Test estimation with no layer info."""
    path = tmp_path / "test.gguf"
    
    metadata = {}
    tensors = [("dummy", [100], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    est = estimate(gguf, ctx=1024, kv='f16')
    
    # With no layer info, KV cache should be 0
    assert est.kv_cache_bytes == 0


def test_estimate_gqa_vs_mha(tmp_path):
    """Test that GQA (grouped query attention) affects KV cache."""
    path_mha = tmp_path / "mha.gguf"
    path_gqa = tmp_path / "gqa.gguf"
    
    # MHA: n_kv_heads = n_heads
    metadata_mha = {
        "general.architecture": "llama",
        "llama.block_count": 2,
        "llama.embedding_length": 128,
        "llama.attention.head_count": 8,
        "llama.attention.head_count_kv": 8,  # Same as n_heads
    }
    
    # GQA: n_kv_heads < n_heads
    metadata_gqa = {
        "general.architecture": "llama",
        "llama.block_count": 2,
        "llama.embedding_length": 128,
        "llama.attention.head_count": 8,
        "llama.attention.head_count_kv": 2,  # 1/4 of n_heads
    }
    
    tensors = [("dummy", [1], GGMLType.F32)]
    
    write_gguf(path_mha, version=3, metadata=metadata_mha, tensors=tensors)
    write_gguf(path_gqa, version=3, metadata=metadata_gqa, tensors=tensors)
    
    gguf_mha = read_gguf(path_mha)
    gguf_gqa = read_gguf(path_gqa)
    
    est_mha = estimate(gguf_mha, ctx=1024, kv='f16')
    est_gqa = estimate(gguf_gqa, ctx=1024, kv='f16')
    
    # GQA should use 1/4 the KV cache (2 KV heads vs 8)
    assert est_gqa.kv_cache_bytes * 4 == est_mha.kv_cache_bytes
