"""GGUF fit analyzer - parse GGUF files and estimate memory requirements."""

from .reader import read_gguf
from .summary import summarize, ModelSummary
from .estimate import estimate, MemoryEstimate
from .plan import plan_fit, max_context, FitPlan
from .compare import compare
from .types import GGUFFile, TensorInfo
from .errors import GGUFError
from .units import parse_size, format_size

__version__ = "0.1.0"

__all__ = [
    'read_gguf',
    'summarize',
    'estimate',
    'plan_fit',
    'max_context',
    'compare',
    'GGUFFile',
    'TensorInfo',
    'ModelSummary',
    'MemoryEstimate',
    'FitPlan',
    'GGUFError',
    'parse_size',
    'format_size',
]
