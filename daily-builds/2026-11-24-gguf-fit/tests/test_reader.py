"""Test basic GGUF reader functionality."""

import pytest
from gguf_fit.reader import read_gguf
from gguf_fit.writer import write_gguf
from gguf_fit.types import GGMLType


def test_read_basic_v3(tmp_path):
    """Test reading basic v3 GGUF file."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.name": "test-model",
        "test.value": 42,
    }
    
    tensors = [
        ("tensor1", [100, 200], GGMLType.F32),
        ("tensor2", [50], GGMLType.Q4_0),
    ]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    assert gguf.version == 3
    assert gguf.tensor_count == 2
    assert len(gguf.tensors) == 2
    assert gguf.metadata["general.name"] == "test-model"
    assert gguf.metadata["test.value"] == 42


def test_read_tensor_dimensions(tmp_path):
    """Test that tensor dimensions are correctly read."""
    path = tmp_path / "test.gguf"
    
    metadata = {}
    tensors = [
        ("t1", [10], GGMLType.F32),
        ("t2", [5, 10], GGMLType.F16),
        ("t3", [2, 3, 4], GGMLType.Q8_0),
    ]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    assert gguf.tensors[0].dims == [10]
    assert gguf.tensors[0].n_dims == 1
    
    assert gguf.tensors[1].dims == [5, 10]
    assert gguf.tensors[1].n_dims == 2
    
    assert gguf.tensors[2].dims == [2, 3, 4]
    assert gguf.tensors[2].n_dims == 3


def test_read_tensor_n_elements(tmp_path):
    """Test tensor element count calculation."""
    path = tmp_path / "test.gguf"
    
    metadata = {}
    tensors = [
        ("t1", [10], GGMLType.F32),
        ("t2", [5, 10], GGMLType.F32),
        ("t3", [2, 3, 4], GGMLType.F32),
    ]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    assert gguf.tensors[0].n_elements == 10
    assert gguf.tensors[1].n_elements == 50
    assert gguf.tensors[2].n_elements == 24


def test_read_tensor_size_bytes(tmp_path):
    """Test tensor size calculation."""
    path = tmp_path / "test.gguf"
    
    metadata = {}
    tensors = [
        ("t_f32", [100], GGMLType.F32),  # 100 * 4 = 400
        ("t_f16", [100], GGMLType.F16),  # 100 * 2 = 200
        ("t_q4", [32], GGMLType.Q4_0),   # 32 / 32 * 18 = 18
    ]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    assert gguf.tensors[0].size_bytes == 400
    assert gguf.tensors[1].size_bytes == 200
    assert gguf.tensors[2].size_bytes == 18


def test_read_alignment(tmp_path):
    """Test alignment reading."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.alignment": 64,
    }
    
    tensors = [("t", [10], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors, alignment=64)
    gguf = read_gguf(path)
    
    assert gguf.alignment == 64
    assert gguf.data_offset % 64 == 0


def test_read_default_alignment(tmp_path):
    """Test default alignment when not specified."""
    path = tmp_path / "test.gguf"
    
    metadata = {}
    tensors = [("t", [10], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    assert gguf.alignment == 32  # Default
    assert gguf.data_offset % 32 == 0


def test_read_empty_string(tmp_path):
    """Test reading empty string metadata."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "empty": "",
    }
    
    tensors = [("t", [1], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    assert gguf.metadata["empty"] == ""


def test_read_empty_array(tmp_path):
    """Test reading empty array metadata."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "empty_array": [],
    }
    
    tensors = [("t", [1], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    assert gguf.metadata["empty_array"] == []


def test_read_file_size(tmp_path):
    """Test that file size is recorded."""
    path = tmp_path / "test.gguf"
    
    metadata = {}
    tensors = [("t", [1000], GGMLType.F32)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    actual_size = path.stat().st_size
    assert gguf.file_size == actual_size


def test_read_unknown_ggml_type(tmp_path):
    """Test that unknown GGML types are handled gracefully."""
    import struct
    
    path = tmp_path / "unknown_type.gguf"
    
    # Manually create a GGUF with an unknown type
    with open(path, 'wb') as f:
        # Magic
        f.write(struct.pack('<I', 0x46554747))
        # Version
        f.write(struct.pack('<I', 3))
        # Tensor count
        f.write(struct.pack('<Q', 1))
        # Metadata count
        f.write(struct.pack('<Q', 0))
        
        # Tensor info with unknown type
        # Name
        f.write(struct.pack('<Q', 1))
        f.write(b't')
        # n_dims
        f.write(struct.pack('<I', 1))
        # dims
        f.write(struct.pack('<Q', 10))
        # Type (use a very high number unlikely to be valid)
        f.write(struct.pack('<I', 999))
        # Offset
        f.write(struct.pack('<Q', 0))
        
        # Padding to alignment
        current = f.tell()
        if current % 32 != 0:
            f.write(b'\x00' * (32 - (current % 32)))
        
        # No tensor data needed
    
    gguf = read_gguf(path)
    
    # Should not crash, type stored as int
    assert gguf.tensors[0].ggml_type == 999
    assert gguf.tensors[0].size_bytes == 0  # Unknown type, can't calculate size
