"""GGUF type definitions and constants."""

from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class GGUFValueType(IntEnum):
    """GGUF metadata value types."""
    UINT8 = 0
    INT8 = 1
    UINT16 = 2
    INT16 = 3
    UINT32 = 4
    INT32 = 5
    FLOAT32 = 6
    BOOL = 7
    STRING = 8
    ARRAY = 9
    UINT64 = 10
    INT64 = 11
    FLOAT64 = 12


class GGMLType(IntEnum):
    """GGML tensor types."""
    F32 = 0
    F16 = 1
    Q4_0 = 2
    Q4_1 = 3
    Q5_0 = 6
    Q5_1 = 7
    Q8_0 = 8
    Q8_1 = 9
    Q2_K = 10
    Q3_K = 11
    Q4_K = 12
    Q5_K = 13
    Q6_K = 14
    Q8_K = 15
    IQ2_XXS = 16
    IQ2_XS = 17
    IQ3_XXS = 18
    IQ1_S = 19
    IQ4_NL = 20
    IQ3_S = 21
    IQ2_S = 22
    IQ4_XS = 23
    I8 = 24
    I16 = 25
    I32 = 26
    I64 = 27
    F64 = 28
    IQ1_M = 29
    BF16 = 30


# Quantization details: (block_size, bytes_per_block)
QUANT_INFO = {
    GGMLType.F32: (1, 4),
    GGMLType.F16: (1, 2),
    GGMLType.BF16: (1, 2),
    GGMLType.Q4_0: (32, 18),
    GGMLType.Q4_1: (32, 20),
    GGMLType.Q5_0: (32, 22),
    GGMLType.Q5_1: (32, 24),
    GGMLType.Q8_0: (32, 34),
    GGMLType.Q8_1: (32, 36),
    GGMLType.Q2_K: (256, 82),
    GGMLType.Q3_K: (256, 110),
    GGMLType.Q4_K: (256, 144),
    GGMLType.Q5_K: (256, 176),
    GGMLType.Q6_K: (256, 210),
    GGMLType.Q8_K: (256, 292),
    GGMLType.IQ2_XXS: (256, 66),
    GGMLType.IQ2_XS: (256, 74),
    GGMLType.IQ3_XXS: (256, 98),
    GGMLType.IQ1_S: (256, 50),
    GGMLType.IQ4_NL: (32, 18),
    GGMLType.IQ3_S: (256, 106),
    GGMLType.IQ2_S: (256, 82),
    GGMLType.IQ4_XS: (256, 136),
    GGMLType.I8: (1, 1),
    GGMLType.I16: (1, 2),
    GGMLType.I32: (1, 4),
    GGMLType.I64: (1, 8),
    GGMLType.F64: (1, 8),
    GGMLType.IQ1_M: (256, 56),
}


def get_type_size(ggml_type: GGMLType, n_elements: int) -> int:
    """Calculate tensor size in bytes."""
    if ggml_type in QUANT_INFO:
        block_size, bytes_per_block = QUANT_INFO[ggml_type]
        return (n_elements // block_size) * bytes_per_block
    return 0


def get_bits_per_weight(ggml_type: GGMLType) -> float:
    """Calculate effective bits per weight."""
    if ggml_type not in QUANT_INFO:
        return 0.0
    block_size, bytes_per_block = QUANT_INFO[ggml_type]
    return (bytes_per_block * 8) / block_size


@dataclass
class TensorInfo:
    """Tensor metadata."""
    name: str
    n_dims: int
    dims: list[int]
    ggml_type: GGMLType | int
    offset: int
    
    @property
    def n_elements(self) -> int:
        """Total number of elements."""
        result = 1
        for d in self.dims:
            result *= d
        return result
    
    @property
    def size_bytes(self) -> int:
        """Tensor size in bytes."""
        if not isinstance(self.ggml_type, GGMLType):
            # Unknown type (stored as raw int), can't calculate size
            return 0
        return get_type_size(self.ggml_type, self.n_elements)


@dataclass
class GGUFFile:
    """Parsed GGUF file."""
    version: int
    tensor_count: int
    metadata: dict[str, Any]
    tensors: list[TensorInfo]
    alignment: int
    data_offset: int
    file_size: int
