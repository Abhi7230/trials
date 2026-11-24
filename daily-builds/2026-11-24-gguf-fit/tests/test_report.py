"""Test report formatting."""

import json
from gguf_fit.writer import write_gguf
from gguf_fit.reader import read_gguf
from gguf_fit.summary import summarize
from gguf_fit.estimate import estimate
from gguf_fit.plan import plan_fit
from gguf_fit import report
from gguf_fit.types import GGMLType


def test_text_format_summary(tmp_path):
    """Test text summary format."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "general.name": "test-model",
    }
    
    tensors = [("t", [100], GGMLType.Q4_0)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    summary = summarize(gguf)
    
    text = report.text.format_summary(summary)
    
    assert "Model Summary" in text
    assert "llama" in text
    assert "test-model" in text


def test_json_format_summary(tmp_path):
    """Test JSON summary format."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "gpt2",
    }
    
    tensors = [("t", [100], GGMLType.F16)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    summary = summarize(gguf)
    
    json_text = report.json.format_summary(summary)
    data = json.loads(json_text)
    
    assert data["architecture"] == "gpt2"
    assert "total_params" in data
    assert "effective_bpw" in data


def test_json_stability(tmp_path):
    """Test that JSON output is stable across runs."""
    path = tmp_path / "test.gguf"
    
    metadata = {"test": "value"}
    tensors = [("t", [50], GGMLType.Q8_0)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf1 = read_gguf(path)
    gguf2 = read_gguf(path)
    
    summary1 = summarize(gguf1)
    summary2 = summarize(gguf2)
    
    json1 = report.json.format_summary(summary1)
    json2 = report.json.format_summary(summary2)
    
    # Should be byte-identical
    assert json1 == json2


def test_markdown_format_plan(tmp_path):
    """Test Markdown plan format."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "llama.block_count": 4,
    }
    
    tensors = [("t", [1000], GGMLType.Q4_0)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    plan = plan_fit(gguf, vram='24GiB', ram='32GiB')
    
    md = report.markdown.format_plan(plan)
    
    assert "# Fit Plan" in md
    assert "Verdict" in md


def test_all_formats_comparison(tmp_path):
    """Test that all formats work for comparison."""
    path_a = tmp_path / "a.gguf"
    path_b = tmp_path / "b.gguf"
    
    metadata = {}
    tensors = [("t", [100], GGMLType.Q4_0)]
    
    write_gguf(path_a, version=3, metadata=metadata, tensors=tensors)
    write_gguf(path_b, version=3, metadata=metadata, tensors=tensors)
    
    from gguf_fit.compare import compare
    comp = compare(path_a, path_b)
    
    text = report.text.format_comparison(comp)
    json_text = report.json.format_comparison(comp)
    md = report.markdown.format_comparison(comp)
    
    assert "Comparison" in text or "comparison" in text.lower()
    
    data = json.loads(json_text)
    assert "model_a" in data
    assert "model_b" in data
    
    assert "Comparison" in md


def test_text_format_with_metadata(tmp_path):
    """Test text format with various metadata fields."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "general.name": "test-model",
        "llama.block_count": 32,
        "llama.embedding_length": 4096,
        "llama.attention.head_count": 32,
        "llama.attention.head_count_kv": 8,
        "llama.context_length": 32768,
        "llama.vocab_size": 32000,
    }
    
    tensors = [("t", [1000], GGMLType.Q4_0)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    summary = summarize(gguf)
    
    text = report.text.format_summary(summary, show_tensors=True)
    
    assert "llama" in text
    assert "32" in text
    assert "4096" in text


def test_markdown_format_estimate(tmp_path):
    """Test Markdown estimate format."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "llama.block_count": 4,
        "llama.embedding_length": 128,
        "llama.attention.head_count": 8,
        "llama.attention.head_count_kv": 2,
    }
    
    tensors = [("t", [1000], GGMLType.Q4_0)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    est = estimate(gguf, ctx=2048, kv='f16')
    md = report.markdown.format_estimate(est)
    
    assert "Memory Estimate" in md
    assert "Context Length" in md
    assert "2048" in md


def test_json_format_plan(tmp_path):
    """Test JSON plan format."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "llama.block_count": 4,
    }
    
    tensors = [("t", [1000], GGMLType.Q4_0)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    plan = plan_fit(gguf, vram='24GiB', ram='32GiB')
    json_text = report.json.format_plan(plan)
    
    data = json.loads(json_text)
    assert "verdict" in data
    assert "estimate" in data


def test_all_format_combinations(tmp_path):
    """Test all report formats for all data types."""
    path = tmp_path / "test.gguf"
    
    metadata = {
        "general.architecture": "llama",
        "llama.block_count": 2,
        "llama.embedding_length": 128,
        "llama.attention.head_count": 4,
        "llama.attention.head_count_kv": 2,
    }
    
    tensors = [("t", [1000], GGMLType.Q4_0)]
    
    write_gguf(path, version=3, metadata=metadata, tensors=tensors)
    gguf = read_gguf(path)
    
    summary = summarize(gguf)
    est = estimate(gguf, ctx=1024, kv='f16')
    plan = plan_fit(gguf, vram='8GiB', ram='16GiB', ctx=1024, kv='f16')
    
    # Test all formats for all types
    for module in [report.text, report.json, report.markdown]:
        s_out = module.format_summary(summary)
        e_out = module.format_estimate(est)
        p_out = module.format_plan(plan)
        
        assert len(s_out) > 0
        assert len(e_out) > 0
        assert len(p_out) > 0
