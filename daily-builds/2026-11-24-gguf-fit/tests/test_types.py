"""Test type utilities."""

import pytest
from gguf_fit.types import GGMLType, get_type_size, get_bits_per_weight, QUANT_INFO


def test_quant_info_q4_0():
    """Test Q4_0 quantization info."""
    block_size, bytes_per_block = QUANT_INFO[GGMLType.Q4_0]
    assert block_size == 32
    assert bytes_per_block == 18


def test_quant_info_q8_0():
    """Test Q8_0 quantization info."""
    block_size, bytes_per_block = QUANT_INFO[GGMLType.Q8_0]
    assert block_size == 32
    assert bytes_per_block == 34


def test_quant_info_f16():
    """Test F16 quantization info."""
    block_size, bytes_per_block = QUANT_INFO[GGMLType.F16]
    assert block_size == 1
    assert bytes_per_block == 2


def test_quant_info_q4_k():
    """Test Q4_K quantization info."""
    block_size, bytes_per_block = QUANT_INFO[GGMLType.Q4_K]
    assert block_size == 256
    assert bytes_per_block == 144


def test_quant_info_q6_k():
    """Test Q6_K quantization info."""
    block_size, bytes_per_block = QUANT_INFO[GGMLType.Q6_K]
    assert block_size == 256
    assert bytes_per_block == 210


def test_get_type_size():
    """Test tensor size calculation."""
    # Q4_0: 32 elements per 18 bytes
    assert get_type_size(GGMLType.Q4_0, 32) == 18
    assert get_type_size(GGMLType.Q4_0, 64) == 36
    assert get_type_size(GGMLType.Q4_0, 1024) == 576
    
    # Q8_0: 32 elements per 34 bytes
    assert get_type_size(GGMLType.Q8_0, 32) == 34
    assert get_type_size(GGMLType.Q8_0, 64) == 68
    
    # F16: 1 element per 2 bytes
    assert get_type_size(GGMLType.F16, 1) == 2
    assert get_type_size(GGMLType.F16, 1000) == 2000


def test_get_bits_per_weight():
    """Test bits per weight calculation."""
    # Q4_0: 18 bytes * 8 bits / 32 elements = 4.5 bpw
    assert get_bits_per_weight(GGMLType.Q4_0) == pytest.approx(4.5)
    
    # Q8_0: 34 bytes * 8 bits / 32 elements = 8.5 bpw
    assert get_bits_per_weight(GGMLType.Q8_0) == pytest.approx(8.5)
    
    # F16: 2 bytes * 8 bits / 1 element = 16 bpw
    assert get_bits_per_weight(GGMLType.F16) == pytest.approx(16.0)
    
    # F32: 4 bytes * 8 bits / 1 element = 32 bpw
    assert get_bits_per_weight(GGMLType.F32) == pytest.approx(32.0)


def test_all_quant_types_have_info():
    """Test that all major quant types have info."""
    required_types = [
        GGMLType.F32, GGMLType.F16, GGMLType.BF16,
        GGMLType.Q4_0, GGMLType.Q4_1, GGMLType.Q5_0, GGMLType.Q5_1,
        GGMLType.Q8_0, GGMLType.Q8_1,
        GGMLType.Q2_K, GGMLType.Q3_K, GGMLType.Q4_K, GGMLType.Q5_K, GGMLType.Q6_K,
    ]
    for qtype in required_types:
        assert qtype in QUANT_INFO, f"{qtype.name} missing from QUANT_INFO"
