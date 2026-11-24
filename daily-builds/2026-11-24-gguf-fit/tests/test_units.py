"""Test size unit parsing."""

import pytest
from gguf_fit.units import parse_size, format_size
from gguf_fit.errors import GGUFError


def test_parse_size_binary():
    """Test binary unit parsing (1024-based)."""
    assert parse_size('1KiB') == 1024
    assert parse_size('1MiB') == 1024**2
    assert parse_size('1GiB') == 1024**3
    assert parse_size('24GiB') == 24 * 1024**3
    assert parse_size('1TiB') == 1024**4


def test_parse_size_decimal():
    """Test decimal unit parsing (1000-based)."""
    assert parse_size('1KB') == 1000
    assert parse_size('1MB') == 1000**2
    assert parse_size('1GB') == 1000**3
    assert parse_size('24GB') == 24 * 1000**3
    assert parse_size('1TB') == 1000**4


def test_parse_size_bare_number():
    """Test bare number parsing."""
    assert parse_size('1024') == 1024
    assert parse_size('1000000') == 1000000


def test_parse_size_int_passthrough():
    """Test integer passthrough."""
    assert parse_size(1024) == 1024


def test_parse_size_case_insensitive():
    """Test case insensitive parsing."""
    assert parse_size('24gib') == 24 * 1024**3
    assert parse_size('24GIB') == 24 * 1024**3


def test_parse_size_invalid():
    """Test invalid size strings."""
    with pytest.raises(GGUFError):
        parse_size('invalid')
    with pytest.raises(GGUFError):
        parse_size('24 XB')
    with pytest.raises(GGUFError):
        parse_size('')


def test_format_size():
    """Test size formatting."""
    assert format_size(1024**3) == "1.00 GiB"
    assert format_size(24 * 1024**3) == "24.00 GiB"
    assert format_size(1536) == "0.00 GiB"
    assert format_size(500 * 1024**2) == "0.49 GiB"
