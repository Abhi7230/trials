"""Model summary generation."""

from collections import Counter
from dataclasses import dataclass

from .types import GGMLType, GGUFFile, get_bits_per_weight


@dataclass
class ModelSummary:
    """Model summary statistics."""
    architecture: str | None
    name: str | None
    n_layers: int | None
    embedding_length: int | None
    n_heads: int | None
    n_kv_heads: int | None
    context_length: int | None
    expert_count: int | None
    vocab_size: int | None
    rope_freq_base: float | None
    rope_freq_scale: float | None
    sliding_window: int | None
    total_params: int
    file_size: int
    total_tensor_bytes: int
    type_histogram: dict[str, int]
    effective_bpw: float
    largest_tensors: list[tuple[str, int, str]]


def summarize(gguf: GGUFFile, top_tensors: int = 10) -> ModelSummary:
    """Generate model summary from GGUF file.
    
    Args:
        gguf: Parsed GGUF file
        top_tensors: Number of largest tensors to include
        
    Returns:
        Model summary
    """
    m = gguf.metadata
    
    # Extract architecture metadata
    architecture = m.get('general.architecture')
    name = m.get('general.name')
    
    # Try architecture-prefixed keys first, then generic
    def get_arch_key(suffix: str, default=None):
        if architecture:
            key = f"{architecture}.{suffix}"
            if key in m:
                return m[key]
        return m.get(suffix, default)
    
    n_layers = get_arch_key('block_count')
    embedding_length = get_arch_key('embedding_length')
    n_heads = get_arch_key('attention.head_count')
    n_kv_heads = get_arch_key('attention.head_count_kv')
    context_length = get_arch_key('context_length')
    expert_count = get_arch_key('expert_count')
    vocab_size = m.get(f"{architecture}.vocab_size") if architecture else None
    rope_freq_base = get_arch_key('rope.freq_base')
    rope_freq_scale = get_arch_key('rope.scale_linear')
    sliding_window = get_arch_key('attention.sliding_window')
    
    # Calculate totals
    total_params = 0
    total_tensor_bytes = 0
    type_counter = Counter()
    
    for tensor in gguf.tensors:
        total_params += tensor.n_elements
        size = tensor.size_bytes
        total_tensor_bytes += size
        
        if isinstance(tensor.ggml_type, GGMLType):
            type_name = tensor.ggml_type.name
        else:
            type_name = f"unknown({tensor.ggml_type})"
        
        type_counter[type_name] += 1
    
    # Calculate effective bpw
    if total_params > 0:
        effective_bpw = (total_tensor_bytes * 8) / total_params
    else:
        effective_bpw = 0.0
    
    # Find largest tensors
    tensors_with_size = []
    for tensor in gguf.tensors:
        if isinstance(tensor.ggml_type, GGMLType):
            type_name = tensor.ggml_type.name
        else:
            type_name = f"unknown({tensor.ggml_type})"
        tensors_with_size.append((tensor.name, tensor.size_bytes, type_name))
    
    tensors_with_size.sort(key=lambda x: x[1], reverse=True)
    largest_tensors = tensors_with_size[:top_tensors]
    
    return ModelSummary(
        architecture=architecture,
        name=name,
        n_layers=n_layers,
        embedding_length=embedding_length,
        n_heads=n_heads,
        n_kv_heads=n_kv_heads,
        context_length=context_length,
        expert_count=expert_count,
        vocab_size=vocab_size,
        rope_freq_base=rope_freq_base,
        rope_freq_scale=rope_freq_scale,
        sliding_window=sliding_window,
        total_params=total_params,
        file_size=gguf.file_size,
        total_tensor_bytes=total_tensor_bytes,
        type_histogram=dict(type_counter),
        effective_bpw=effective_bpw,
        largest_tensors=largest_tensors,
    )
