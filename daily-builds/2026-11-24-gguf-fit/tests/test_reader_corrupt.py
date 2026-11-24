"""Test reader with corrupt/malicious input."""

import pytest
import struct
from pathlib import Path
from gguf_fit.reader import read_gguf
from gguf_fit.errors import GGUFError


def test_empty_file(tmp_path):
    """Test reading empty file."""
    path = tmp_path / "empty.gguf"
    path.write_bytes(b'')
    
    with pytest.raises(GGUFError, match="empty"):
        read_gguf(path)


def test_bad_magic(tmp_path):
    """Test reading file with bad magic bytes."""
    path = tmp_path / "bad_magic.gguf"
    path.write_bytes(b'BAAD' + b'\x00' * 100)
    
    with pytest.raises(GGUFError, match="Invalid magic"):
        read_gguf(path)


def test_unsupported_version(tmp_path):
    """Test reading file with unsupported version."""
    path = tmp_path / "bad_version.gguf"
    data = struct.pack('<I', 0x46554747)  # Magic
    data += struct.pack('<I', 999)  # Bad version
    data += b'\x00' * 100
    path.write_bytes(data)
    
    with pytest.raises(GGUFError, match="Unsupported.*version"):
        read_gguf(path)


def test_big_endian_detection(tmp_path):
    """Test detection of big-endian files."""
    path = tmp_path / "big_endian.gguf"
    data = struct.pack('<I', 0x46554747)  # Magic (little-endian)
    data += struct.pack('>I', 3)  # Version in big-endian (will appear as large number)
    data += b'\x00' * 100
    path.write_bytes(data)
    
    with pytest.raises(GGUFError, match="Big-endian"):
        read_gguf(path)


@pytest.mark.parametrize("truncate_at", [4, 8, 16, 20, 24, 32, 40, 50])
def test_truncated_file(tmp_path, truncate_at):
    """Test reading truncated files at various offsets."""
    path = tmp_path / f"truncated_{truncate_at}.gguf"
    
    # Build a partial valid header
    data = struct.pack('<I', 0x46554747)  # Magic
    data += struct.pack('<I', 3)  # Version
    data += struct.pack('<Q', 1)  # Tensor count
    data += struct.pack('<Q', 1)  # Metadata count
    data += struct.pack('<Q', 10)  # String length
    data += b'test.value'  # String
    data += struct.pack('<I', 4)  # Value type (UINT32)
    data += struct.pack('<I', 42)  # Value
    
    # Truncate
    path.write_bytes(data[:truncate_at])
    
    with pytest.raises(GGUFError, match="Unexpected end"):
        read_gguf(path)


def test_absurd_string_length(tmp_path):
    """Test reading file with absurdly large string length."""
    path = tmp_path / "huge_string.gguf"
    
    data = struct.pack('<I', 0x46554747)  # Magic
    data += struct.pack('<I', 3)  # Version
    data += struct.pack('<Q', 0)  # Tensor count
    data += struct.pack('<Q', 1)  # Metadata count
    data += struct.pack('<Q', 2**60)  # Absurd string length
    
    path.write_bytes(data)
    
    with pytest.raises(GGUFError, match="String length.*exceeds"):
        read_gguf(path)


def test_absurd_tensor_count(tmp_path):
    """Test reading file with absurdly large tensor count."""
    path = tmp_path / "huge_tensor_count.gguf"
    
    data = struct.pack('<I', 0x46554747)  # Magic
    data += struct.pack('<I', 3)  # Version
    data += struct.pack('<Q', 2**60)  # Absurd tensor count
    
    path.write_bytes(data)
    
    with pytest.raises(GGUFError, match="Tensor count.*exceeds"):
        read_gguf(path)


def test_absurd_array_length(tmp_path):
    """Test reading file with absurdly large array length."""
    path = tmp_path / "huge_array.gguf"
    
    data = struct.pack('<I', 0x46554747)  # Magic
    data += struct.pack('<I', 3)  # Version
    data += struct.pack('<Q', 0)  # Tensor count
    data += struct.pack('<Q', 1)  # Metadata count
    
    # Key
    data += struct.pack('<Q', 4)  # Key length
    data += b'test'
    
    # Array value
    data += struct.pack('<I', 9)  # ARRAY type
    data += struct.pack('<I', 4)  # Element type (UINT32)
    data += struct.pack('<Q', 2**60)  # Absurd array length
    
    path.write_bytes(data)
    
    with pytest.raises(GGUFError, match="Array length.*exceeds"):
        read_gguf(path)


def test_invalid_utf8(tmp_path):
    """Test reading file with invalid UTF-8."""
    path = tmp_path / "bad_utf8.gguf"
    
    data = struct.pack('<I', 0x46554747)  # Magic
    data += struct.pack('<I', 3)  # Version
    data += struct.pack('<Q', 0)  # Tensor count
    data += struct.pack('<Q', 1)  # Metadata count
    
    # Key with invalid UTF-8
    data += struct.pack('<Q', 4)  # String length
    data += b'\xff\xfe\xfd\xfc'  # Invalid UTF-8
    
    path.write_bytes(data)
    
    with pytest.raises(GGUFError, match="Invalid UTF-8"):
        read_gguf(path)


def test_zero_length_file_non_empty(tmp_path):
    """Test that a file with just magic is rejected."""
    path = tmp_path / "tiny.gguf"
    path.write_bytes(struct.pack('<I', 0x46554747))
    
    with pytest.raises(GGUFError, match="Unexpected end"):
        read_gguf(path)
