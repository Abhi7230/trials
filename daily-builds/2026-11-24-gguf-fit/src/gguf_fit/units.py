"""Size unit parsing and formatting."""

import re
from .errors import GGUFError


def parse_size(size_str: str) -> int:
    """Parse size string to bytes.
    
    Supports:
    - Binary: KiB, MiB, GiB, TiB (1024-based)
    - Decimal: KB, MB, GB, TB (1000-based)
    - Bare numbers (interpreted as bytes)
    
    Examples:
        >>> parse_size('24GiB')
        25769803776
        >>> parse_size('24GB')
        24000000000
        >>> parse_size('1024')
        1024
    """
    if isinstance(size_str, int):
        return size_str
    
    size_str = size_str.strip()
    
    # Try bare number
    try:
        return int(size_str)
    except ValueError:
        pass
    
    # Parse with units
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGT]i?B)$', size_str, re.IGNORECASE)
    if not match:
        raise GGUFError(f"Invalid size format: {size_str}")
    
    value_str, unit = match.groups()
    value = float(value_str)
    
    unit = unit.upper()
    
    # Binary units (1024-based)
    if 'I' in unit:
        multipliers = {
            'KIB': 1024,
            'MIB': 1024**2,
            'GIB': 1024**3,
            'TIB': 1024**4,
        }
    # Decimal units (1000-based)
    else:
        multipliers = {
            'KB': 1000,
            'MB': 1000**2,
            'GB': 1000**3,
            'TB': 1000**4,
        }
    
    return int(value * multipliers[unit])


def format_size(bytes_val: int | float, decimal_places: int = 2) -> str:
    """Format bytes as human-readable size in GiB.
    
    Examples:
        >>> format_size(25769803776)
        '24.00 GiB'
        >>> format_size(1536)
        '0.00 GiB'
    """
    gib = bytes_val / (1024**3)
    return f"{gib:.{decimal_places}f} GiB"
