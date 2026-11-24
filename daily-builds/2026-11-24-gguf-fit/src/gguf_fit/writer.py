"""Minimal GGUF writer for test fixtures."""

import struct
from pathlib import Path
from typing import Any, BinaryIO

from .types import GGMLType, GGUFValueType

GGUF_MAGIC = 0x46554747


def write_gguf(
    path: str | Path,
    version: int,
    metadata: dict[str, Any],
    tensors: list[tuple[str, list[int], GGMLType]],
    alignment: int = 32,
    declare_only: bool = False,
) -> None:
    """Write a GGUF file.
    
    Args:
        path: Output path
        version: GGUF version (2 or 3)
        metadata: Metadata dictionary
        tensors: List of (name, dims, type) tuples
        alignment: Tensor data alignment
        declare_only: If True, write header/tensor table but omit tensor data
    """
    with open(path, 'wb') as f:
        # Write magic
        f.write(struct.pack('<I', GGUF_MAGIC))
        
        # Write version
        f.write(struct.pack('<I', version))
        
        # Write counts
        f.write(struct.pack('<Q', len(tensors)))
        f.write(struct.pack('<Q', len(metadata)))
        
        # Write metadata
        for key, value in metadata.items():
            _write_metadata_kv(f, key, value)
        
        # Write tensor info
        tensor_offset = 0
        tensor_sizes = []
        for name, dims, ggml_type in tensors:
            _write_tensor_info(f, name, dims, ggml_type, tensor_offset)
            
            # Calculate tensor size
            n_elements = 1
            for d in dims:
                n_elements *= d
            
            from .types import get_type_size
            size = get_type_size(ggml_type, n_elements)
            tensor_sizes.append(size)
            tensor_offset += size
        
        # Align for data section
        current_offset = f.tell()
        if current_offset % alignment != 0:
            padding = alignment - (current_offset % alignment)
            f.write(b'\x00' * padding)
        
        # Write tensor data (or not, if declare_only)
        if not declare_only:
            for size in tensor_sizes:
                f.write(b'\x00' * size)


def _write_string(f: BinaryIO, s: str) -> None:
    """Write a GGUF string."""
    encoded = s.encode('utf-8')
    f.write(struct.pack('<Q', len(encoded)))
    f.write(encoded)


def _write_value(f: BinaryIO, value: Any, value_type: int | None = None) -> None:
    """Write a metadata value."""
    if value_type is None:
        value_type = _infer_value_type(value)
    
    if value_type == GGUFValueType.UINT8:
        f.write(struct.pack('<B', value))
    elif value_type == GGUFValueType.INT8:
        f.write(struct.pack('<b', value))
    elif value_type == GGUFValueType.UINT16:
        f.write(struct.pack('<H', value))
    elif value_type == GGUFValueType.INT16:
        f.write(struct.pack('<h', value))
    elif value_type == GGUFValueType.UINT32:
        f.write(struct.pack('<I', value))
    elif value_type == GGUFValueType.INT32:
        f.write(struct.pack('<i', value))
    elif value_type == GGUFValueType.FLOAT32:
        f.write(struct.pack('<f', value))
    elif value_type == GGUFValueType.UINT64:
        f.write(struct.pack('<Q', value))
    elif value_type == GGUFValueType.INT64:
        f.write(struct.pack('<q', value))
    elif value_type == GGUFValueType.FLOAT64:
        f.write(struct.pack('<d', value))
    elif value_type == GGUFValueType.BOOL:
        f.write(struct.pack('<?', value))
    elif value_type == GGUFValueType.STRING:
        _write_string(f, value)
    elif value_type == GGUFValueType.ARRAY:
        if not value:
            elem_type = GGUFValueType.UINT8
        else:
            elem_type = _infer_value_type(value[0])
        
        f.write(struct.pack('<I', elem_type))
        f.write(struct.pack('<Q', len(value)))
        for elem in value:
            _write_value(f, elem, elem_type)


def _infer_value_type(value: Any) -> int:
    """Infer GGUF value type from Python value."""
    if isinstance(value, bool):
        return GGUFValueType.BOOL
    elif isinstance(value, str):
        return GGUFValueType.STRING
    elif isinstance(value, list):
        return GGUFValueType.ARRAY
    elif isinstance(value, float):
        return GGUFValueType.FLOAT32
    elif isinstance(value, int):
        if 0 <= value < 2**32:
            return GGUFValueType.UINT32
        else:
            return GGUFValueType.INT64
    else:
        raise ValueError(f"Cannot infer GGUF type for {type(value)}")


def _write_metadata_kv(f: BinaryIO, key: str, value: Any) -> None:
    """Write a metadata key-value pair."""
    _write_string(f, key)
    value_type = _infer_value_type(value)
    f.write(struct.pack('<I', value_type))
    _write_value(f, value, value_type)


def _write_tensor_info(f: BinaryIO, name: str, dims: list[int], ggml_type: GGMLType, offset: int) -> None:
    """Write tensor info."""
    _write_string(f, name)
    f.write(struct.pack('<I', len(dims)))
    for dim in dims:
        f.write(struct.pack('<Q', dim))
    f.write(struct.pack('<I', ggml_type))
    f.write(struct.pack('<Q', offset))
