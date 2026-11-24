"""Test model summary generation."""

import pytest
from gguf_fit.writer import write_gguf
from gguf_fit.reader import read_gguf
from gguf_fit.summary import summarize
from gguf_fit.types import GGMLType


def test_summary_basic(tmp_path):
    """Test basic summary generation."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "general.name": "test-llama",
        "llama.block_count": 32,
        "llama.embedding_length": 4096,
        "llama.attention.head_count": 32,
        "llama.attention.head_count_kv": 8,
        "llama.context_length": 32768,
        "llama.vocab_size": 32000,
    }
    
    tensors = [
        ("token_embd.weight", [32000, 4096], GGMLType.Q4_0),
        ("blk.0.attn_q.weight", [4096, 4096], GGMLType.Q4_0),
        ("output.weight", [4096, 32000], GGMLType.Q4_0),
    ]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    summary = summarize(gguf)
    
    assert summary.architecture == "llama"
    assert summary.name == "test-llama"
    assert summary.n_layers == 32
    assert summary.embedding_length == 4096
    assert summary.n_heads == 32
    assert summary.n_kv_heads == 8
    assert summary.context_length == 32768
    assert summary.vocab_size == 32000


def test_summary_params_and_size(tmp_path):
    """Test parameter counting and size calculation."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
    }
    
    # 1000 * 100 = 100,000 params in F16 = 200,000 bytes
    # 500 * 50 = 25,000 params in Q4_0
    tensors = [
        ("t1", [1000, 100], GGMLType.F16),
        ("t2", [500, 50], GGMLType.Q4_0),
    ]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    summary = summarize(gguf)
    
    assert summary.total_params == 125_000
    
    # F16: 100,000 * 2 bytes = 200,000
    # Q4_0: 25,000 // 32 * 18 = 781 * 18 = 14,058
    expected_bytes = 200_000 + 14_058
    assert summary.total_tensor_bytes == expected_bytes


def test_summary_type_histogram(tmp_path):
    """Test type histogram."""
    path = tmp_path / "test.gguf"
    
    metadata = {}
    tensors = [
        ("t1", [100], GGMLType.Q4_0),
        ("t2", [100], GGMLType.Q4_0),
        ("t3", [100], GGMLType.Q8_0),
        ("t4", [100], GGMLType.F16),
    ]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    summary = summarize(gguf)
    
    assert summary.type_histogram["Q4_0"] == 2
    assert summary.type_histogram["Q8_0"] == 1
    assert summary.type_histogram["F16"] == 1


def test_summary_effective_bpw(tmp_path):
    """Test effective bits per weight calculation."""
    path = tmp_path / "test.gguf"
    
    metadata = {}
    # Pure Q4_0 should give bpw close to 4.5
    tensors = [
        ("t1", [1024], GGMLType.Q4_0),
    ]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    summary = summarize(gguf)
    
    assert summary.effective_bpw == pytest.approx(4.5, abs=0.01)


def test_summary_largest_tensors(tmp_path):
    """Test largest tensors tracking."""
    path = tmp_path / "test.gguf"
    
    metadata = {}
    tensors = [
        ("small", [10], GGMLType.F32),
        ("large", [1000], GGMLType.F32),
        ("medium", [100], GGMLType.F32),
    ]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    summary = summarize(gguf, top_tensors=3)
    
    assert len(summary.largest_tensors) == 3
    assert summary.largest_tensors[0][0] == "large"
    assert summary.largest_tensors[1][0] == "medium"
    assert summary.largest_tensors[2][0] == "small"


def test_summary_moe(tmp_path):
    """Test MoE model summary."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "mixtral",
        "mixtral.expert_count": 8,
        "mixtral.block_count": 32,
    }
    
    tensors = [("dummy", [1], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    summary = summarize(gguf)
    
    assert summary.architecture == "mixtral"
    assert summary.expert_count == 8
    assert summary.n_layers == 32


def test_summary_sliding_window(tmp_path):
    """Test sliding window metadata."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "llama.attention.sliding_window": 4096,
    }
    
    tensors = [("dummy", [1], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    summary = summarize(gguf)
    
    assert summary.sliding_window == 4096
