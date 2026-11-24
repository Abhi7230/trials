"""GGUF file reader."""

import struct
from pathlib import Path
from typing import Any, BinaryIO

from .errors import GGUFError
from .types import GGMLType, GGUFFile, GGUFValueType, TensorInfo

# Safety limits
MAX_STRING_LENGTH = 10_000_000
MAX_ARRAY_LENGTH = 100_000
MAX_TENSOR_COUNT = 100_000

GGUF_MAGIC = 0x46554747  # "GGUF" in little-endian


def read_gguf(path: str | Path) -> GGUFFile:
    """Read and parse a GGUF file (header only, no tensor data).
    
    Args:
        path: Path to GGUF file
        
    Returns:
        Parsed GGUF file structure
        
    Raises:
        GGUFError: On parse errors or invalid format
    """
    path = Path(path)
    file_size = path.stat().st_size
    
    if file_size == 0:
        raise GGUFError("File is empty")
    
    with open(path, 'rb') as f:
        return _parse_gguf(f, file_size)


def _parse_gguf(f: BinaryIO, file_size: int) -> GGUFFile:
    """Parse GGUF from file handle."""
    offset = 0
    
    # Read magic
    magic_bytes = _read_bytes(f, 4, offset)
    magic = struct.unpack('<I', magic_bytes)[0]
    offset += 4
    
    if magic != GGUF_MAGIC:
        raise GGUFError(f"Invalid magic bytes: 0x{magic:08x}, expected 0x{GGUF_MAGIC:08x}", offset=0)
    
    # Read version
    version_bytes = _read_bytes(f, 4, offset)
    version = struct.unpack('<I', version_bytes)[0]
    offset += 4
    
    # Check for big-endian (version would be reversed)
    if version > 1000:
        raise GGUFError(f"Big-endian GGUF files are not supported (version field: {version})", offset=4)
    
    if version not in (2, 3):
        raise GGUFError(f"Unsupported GGUF version: {version}", offset=4)
    
    # Read tensor and metadata counts
    tensor_count_bytes = _read_bytes(f, 8, offset)
    tensor_count = struct.unpack('<Q', tensor_count_bytes)[0]
    offset += 8
    
    if tensor_count > MAX_TENSOR_COUNT:
        raise GGUFError(f"Tensor count {tensor_count} exceeds maximum {MAX_TENSOR_COUNT}", offset=8)
    
    metadata_kv_count_bytes = _read_bytes(f, 8, offset)
    metadata_kv_count = struct.unpack('<Q', metadata_kv_count_bytes)[0]
    offset += 8
    
    # Read metadata
    metadata = {}
    for _ in range(metadata_kv_count):
        key, value, offset = _read_metadata_kv(f, offset, version)
        metadata[key] = value
    
    # Read tensor info
    tensors = []
    for _ in range(tensor_count):
        tensor, offset = _read_tensor_info(f, offset, version)
        tensors.append(tensor)
    
    # Calculate alignment and data offset
    alignment = metadata.get('general.alignment', 32)
    if not isinstance(alignment, int) or alignment <= 0:
        alignment = 32
    
    # Align offset
    if offset % alignment != 0:
        offset += alignment - (offset % alignment)
    
    data_offset = offset
    
    return GGUFFile(
        version=version,
        tensor_count=tensor_count,
        metadata=metadata,
        tensors=tensors,
        alignment=alignment,
        data_offset=data_offset,
        file_size=file_size,
    )


def _read_bytes(f: BinaryIO, n: int, offset: int) -> bytes:
    """Read n bytes, raising GGUFError on truncation."""
    data = f.read(n)
    if len(data) < n:
        raise GGUFError(f"Unexpected end of file: expected {n} bytes, got {len(data)}", offset=offset)
    return data


def _read_string(f: BinaryIO, offset: int) -> tuple[str, int]:
    """Read GGUF string (uint64 length + UTF-8 bytes)."""
    len_bytes = _read_bytes(f, 8, offset)
    length = struct.unpack('<Q', len_bytes)[0]
    offset += 8
    
    if length > MAX_STRING_LENGTH:
        raise GGUFError(f"String length {length} exceeds maximum {MAX_STRING_LENGTH}", offset=offset-8)
    
    if length > 0:
        str_bytes = _read_bytes(f, length, offset)
        offset += length
        try:
            value = str_bytes.decode('utf-8')
        except UnicodeDecodeError as e:
            raise GGUFError(f"Invalid UTF-8 in string: {e}", offset=offset-length)
    else:
        value = ""
    
    return value, offset


def _read_metadata_value(f: BinaryIO, offset: int, value_type: int) -> tuple[Any, int]:
    """Read a metadata value of the given type."""
    vt = value_type
    
    if vt == GGUFValueType.UINT8:
        data = _read_bytes(f, 1, offset)
        return struct.unpack('<B', data)[0], offset + 1
    elif vt == GGUFValueType.INT8:
        data = _read_bytes(f, 1, offset)
        return struct.unpack('<b', data)[0], offset + 1
    elif vt == GGUFValueType.UINT16:
        data = _read_bytes(f, 2, offset)
        return struct.unpack('<H', data)[0], offset + 2
    elif vt == GGUFValueType.INT16:
        data = _read_bytes(f, 2, offset)
        return struct.unpack('<h', data)[0], offset + 2
    elif vt == GGUFValueType.UINT32:
        data = _read_bytes(f, 4, offset)
        return struct.unpack('<I', data)[0], offset + 4
    elif vt == GGUFValueType.INT32:
        data = _read_bytes(f, 4, offset)
        return struct.unpack('<i', data)[0], offset + 4
    elif vt == GGUFValueType.FLOAT32:
        data = _read_bytes(f, 4, offset)
        return struct.unpack('<f', data)[0], offset + 4
    elif vt == GGUFValueType.UINT64:
        data = _read_bytes(f, 8, offset)
        return struct.unpack('<Q', data)[0], offset + 8
    elif vt == GGUFValueType.INT64:
        data = _read_bytes(f, 8, offset)
        return struct.unpack('<q', data)[0], offset + 8
    elif vt == GGUFValueType.FLOAT64:
        data = _read_bytes(f, 8, offset)
        return struct.unpack('<d', data)[0], offset + 8
    elif vt == GGUFValueType.BOOL:
        data = _read_bytes(f, 1, offset)
        return struct.unpack('<?', data)[0], offset + 1
    elif vt == GGUFValueType.STRING:
        return _read_string(f, offset)
    elif vt == GGUFValueType.ARRAY:
        # Read array type
        type_bytes = _read_bytes(f, 4, offset)
        array_type = struct.unpack('<I', type_bytes)[0]
        offset += 4
        
        # Read array length
        len_bytes = _read_bytes(f, 8, offset)
        array_len = struct.unpack('<Q', len_bytes)[0]
        offset += 8
        
        if array_len > MAX_ARRAY_LENGTH:
            raise GGUFError(f"Array length {array_len} exceeds maximum {MAX_ARRAY_LENGTH}", offset=offset-8)
        
        # Read array elements
        array = []
        for _ in range(array_len):
            elem, offset = _read_metadata_value(f, offset, array_type)
            array.append(elem)
        
        return array, offset
    else:
        raise GGUFError(f"Unknown metadata value type: {vt}", offset=offset)


def _read_metadata_kv(f: BinaryIO, offset: int, version: int) -> tuple[str, Any, int]:
    """Read a metadata key-value pair."""
    # Read key
    key, offset = _read_string(f, offset)
    
    # Read value type
    type_bytes = _read_bytes(f, 4, offset)
    value_type = struct.unpack('<I', type_bytes)[0]
    offset += 4
    
    # Read value
    value, offset = _read_metadata_value(f, offset, value_type)
    
    return key, value, offset


def _read_tensor_info(f: BinaryIO, offset: int, version: int) -> tuple[TensorInfo, int]:
    """Read tensor info from tensor table."""
    # Read name
    name, offset = _read_string(f, offset)
    
    # Read n_dimensions
    n_dims_bytes = _read_bytes(f, 4, offset)
    n_dims = struct.unpack('<I', n_dims_bytes)[0]
    offset += 4
    
    if n_dims > 10:
        raise GGUFError(f"Tensor {name}: n_dims {n_dims} is unreasonably large", offset=offset-4)
    
    # Read dimensions
    dims = []
    for _ in range(n_dims):
        dim_bytes = _read_bytes(f, 8, offset)
        dim = struct.unpack('<Q', dim_bytes)[0]
        offset += 8
        dims.append(dim)
    
    # Read type
    type_bytes = _read_bytes(f, 4, offset)
    ggml_type_int = struct.unpack('<I', type_bytes)[0]
    offset += 4
    
    # Try to convert to enum, but keep as int if unknown
    try:
        ggml_type = GGMLType(ggml_type_int)
    except ValueError:
        ggml_type = ggml_type_int
    
    # Read offset
    tensor_offset_bytes = _read_bytes(f, 8, offset)
    tensor_offset = struct.unpack('<Q', tensor_offset_bytes)[0]
    offset += 8
    
    return TensorInfo(
        name=name,
        n_dims=n_dims,
        dims=dims,
        ggml_type=ggml_type,
        offset=tensor_offset,
    ), offset
