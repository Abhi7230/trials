"""Test GGUF writer and reader roundtrip."""

import pytest
from pathlib import Path
from gguf_fit.writer import write_gguf
from gguf_fit.reader import read_gguf
from gguf_fit.types import GGMLType


def test_roundtrip_v2(tmp_path):
    """Test write and read roundtrip for v2."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.name": "test-model",
        "general.architecture": "llama",
        "test.uint32": 42,
        "test.float": 3.14,
        "test.bool": True,
        "test.string": "hello",
    }
    
    tensors = [
        ("tensor1", [10, 20], GGMLType.F16),
        ("tensor2", [5, 5], GGMLType.Q4_0),
    ]
    
    write_gguf(path, version=2, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    assert gguf.version == 2
    assert gguf.tensor_count == 2
    assert gguf.metadata["general.name"] == "test-model"
    assert gguf.metadata["test.uint32"] == 42
    assert gguf.metadata["test.float"] == pytest.approx(3.14)
    assert gguf.metadata["test.bool"] is True
    assert gguf.metadata["test.string"] == "hello"
    
    assert gguf.tensors[0].name == "tensor1"
    assert gguf.tensors[0].dims == [10, 20]
    assert gguf.tensors[0].ggml_type == GGMLType.F16
    
    assert gguf.tensors[1].name == "tensor2"
    assert gguf.tensors[1].dims == [5, 5]
    assert gguf.tensors[1].ggml_type == GGMLType.Q4_0


def test_roundtrip_v3(tmp_path):
    """Test write and read roundtrip for v3."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "gpt2",
    }
    
    tensors = [
        ("wte.weight", [1000, 128], GGMLType.Q8_0),
    ]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    assert gguf.version == 3
    assert gguf.tensor_count == 1


def test_roundtrip_all_value_types(tmp_path):
    """Test roundtrip with all metadata value types."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "test.uint8": 255,
        "test.uint32": 1000000,
        "test.float32": 1.5,
        "test.bool_true": True,
        "test.bool_false": False,
        "test.string": "test string",
        "test.array_int": [1, 2, 3],
        "test.array_string": ["a", "b", "c"],
        "test.nested_array": [[1, 2], [3, 4]],
    }
    
    tensors = [("dummy", [1], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    assert gguf.metadata["test.uint8"] == 255
    assert gguf.metadata["test.uint32"] == 1000000
    assert gguf.metadata["test.float32"] == pytest.approx(1.5)
    assert gguf.metadata["test.bool_true"] is True
    assert gguf.metadata["test.bool_false"] is False
    assert gguf.metadata["test.string"] == "test string"
    assert gguf.metadata["test.array_int"] == [1, 2, 3]
    assert gguf.metadata["test.array_string"] == ["a", "b", "c"]
    assert gguf.metadata["test.nested_array"] == [[1, 2], [3, 4]]


def test_roundtrip_unicode(tmp_path):
    """Test roundtrip with unicode strings."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "test.unicode": "Hello 世界 🌍",
        "test.emoji": "🚀 🎉 ✨",
    }
    
    tensors = [("dummy", [1], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    assert gguf.metadata["test.unicode"] == "Hello 世界 🌍"
    assert gguf.metadata["test.emoji"] == "🚀 🎉 ✨"


def test_roundtrip_alignment(tmp_path):
    """Test that alignment is correctly applied."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.alignment": 64,
    }
    
    tensors = [("tensor", [10], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors, alignment=64)
    gguf = read_gguf(path)
    
    assert gguf.alignment == 64
    assert gguf.data_offset % 64 == 0


def test_roundtrip_data_offset(tmp_path):
    """Test that data offset is correctly computed."""
    path = tmp_path / "test.gguf"
    
    metadata = {"test": "value"}
    tensors = [
        ("t1", [100], GGMLType.F32),
        ("t2", [200], GGMLType.F16),
    ]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    # Data offset should be aligned
    assert gguf.data_offset % 32 == 0
    
    # Tensor offsets should be relative to data section start
    assert gguf.tensors[0].offset == 0
    expected_offset = gguf.tensors[0].size_bytes
    assert gguf.tensors[1].offset == expected_offset
