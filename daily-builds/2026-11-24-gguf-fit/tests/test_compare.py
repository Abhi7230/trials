"""Test model comparison."""

import pytest
from gguf_fit.compare import compare
from gguf_fit.writer import write_gguf
from gguf_fit.types import GGMLType


def test_compare_different_quants(tmp_path):
    """Test comparing models with different quantization types."""
    path_q4 = tmp_path / "model_q4.gguf"
    path_q8 = tmp_path / "model_q8.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "llama.block_count": 4,
    }
    
    # Same structure, different quants
    tensors_q4 = [
        ("t1", [1024], GGMLType.Q4_0),
        ("t2", [1024], GGMLType.Q4_0),
    ]
    
    tensors_q8 = [
        ("t1", [1024], GGMLType.Q8_0),
        ("t2", [1024], GGMLType.Q8_0),
    ]
    
    write_gguf(path_q4, version=3, metadata=metadata, tensors=tensors_q4)
    write_gguf(path_q8, version=3, metadata=metadata, tensors=tensors_q8)
    
    comp = compare(path_q4, path_q8, ctx=8192, kv='f16')
    
    # Both should have same params
    assert comp.model_a.total_params == comp.model_b.total_params
    
    # Q4_0 should have lower bpw than Q8_0
    assert comp.model_a.effective_bpw < comp.model_b.effective_bpw
    
    # Q4_0 should have smaller file size
    assert comp.model_a.file_size < comp.model_b.file_size
    
    # Type histograms should differ
    assert comp.model_a.type_histogram['Q4_0'] == 2
    assert comp.model_b.type_histogram['Q8_0'] == 2


def test_compare_bpw_accuracy(tmp_path):
    """Test that reported bpw is within spec tolerance."""
    path_q4 = tmp_path / "q4.gguf"
    path_q8 = tmp_path / "q8.gguf"
    
    metadata = {}
    tensors_q4 = [("t", [1024], GGMLType.Q4_0)]
    tensors_q8 = [("t", [1024], GGMLType.Q8_0)]
    
    write_gguf(path_q4, version=3, metadata=metadata, tensors=tensors_q4)
    write_gguf(path_q8, version=3, metadata=metadata, tensors=tensors_q8)
    
    comp = compare(path_q4, path_q8)
    
    # Q4_0 should be ~4.5 bpw
    assert abs(comp.model_a.effective_bpw - 4.5) < 0.01
    
    # Q8_0 should be ~8.5 bpw
    assert abs(comp.model_b.effective_bpw - 8.5) < 0.01


def test_compare_memory_at_context(tmp_path):
    """Test that memory estimates differ based on context."""
    path_a = tmp_path / "a.gguf"
    path_b = tmp_path / "b.gguf"
    
    metadata_a = {
        "general.architecture": "llama",
        "llama.block_count": 2,
        "llama.embedding_length": 128,
        "llama.attention.head_count": 4,
        "llama.attention.head_count_kv": 2,
    }
    
    metadata_b = {
        "general.architecture": "llama",
        "llama.block_count": 4,  # More layers
        "llama.embedding_length": 128,
        "llama.attention.head_count": 4,
        "llama.attention.head_count_kv": 2,
    }
    
    tensors = [("t", [100], GGMLType.F32)]
    
    write_gguf(path_a, version=3, metadata=metadata_a, tensors=tensors)
    write_gguf(path_b, version=3, metadata=metadata_b, tensors=tensors)
    
    comp = compare(path_a, path_b, ctx=8192, kv='f16')
    
    # Model B has more layers, so more KV cache
    assert comp.model_b.memory_at_ctx > comp.model_a.memory_at_ctx


def test_compare_type_differences(tmp_path):
    """Test that type differences are detected."""
    path_a = tmp_path / "a.gguf"
    path_b = tmp_path / "b.gguf"
    
    metadata = {}
    
    tensors_a = [
        ("t1", [100], GGMLType.Q4_0),
        ("t2", [100], GGMLType.F16),
    ]
    
    tensors_b = [
        ("t1", [100], GGMLType.Q8_0),
        ("t2", [100], GGMLType.Q8_0),
    ]
    
    write_gguf(path_a, version=3, metadata=metadata, tensors=tensors_a)
    write_gguf(path_b, version=3, metadata=metadata, tensors=tensors_b)
    
    comp = compare(path_a, path_b)
    
    # Different type distributions
    assert comp.model_a.type_histogram != comp.model_b.type_histogram
    assert 'Q4_0' in comp.model_a.type_histogram
    assert 'Q8_0' in comp.model_b.type_histogram
