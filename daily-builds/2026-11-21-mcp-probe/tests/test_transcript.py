"""Tests for transcript handling."""

import pytest
import tempfile
import json
from pathlib import Path
from mcp_probe.transcript import TranscriptRecorder, load_transcript, check_transcript_static


def test_transcript_recorder():
    """Test recording transcript."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        temp_path = f.name
    
    try:
        recorder = TranscriptRecorder(temp_path)
        recorder.start()
        
        recorder.record_request({"method": "initialize", "id": 1})
        recorder.record_response({"jsonrpc": "2.0", "id": 1, "result": {}})
        
        recorder.stop()
        
        transcript = load_transcript(temp_path)
        assert len(transcript) == 2
        assert transcript[0]["type"] == "request"
        assert transcript[1]["type"] == "response"
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_load_transcript():
    """Test loading transcript from file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"type": "request", "data": {"method": "test"}}\n')
        f.write('{"type": "response", "data": {"result": {}}}\n')
        temp_path = f.name
    
    try:
        transcript = load_transcript(temp_path)
        assert len(transcript) == 2
        assert transcript[0]["type"] == "request"
        assert transcript[1]["type"] == "response"
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_check_transcript_static():
    """Test static checking of transcript."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        tools_response = {
            "type": "response",
            "data": {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "tools": [
                        {
                            "name": "valid_tool",
                            "description": "A valid tool with proper description",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "param": {"type": "string", "description": "A parameter"}
                                }
                            }
                        }
                    ]
                }
            }
        }
        f.write(json.dumps(tools_response) + "\n")
        temp_path = f.name
    
    try:
        report = check_transcript_static(temp_path)
        assert "score" in report
        assert "grade" in report
        assert report["stats"]["tool_count"] == 1
    finally:
        Path(temp_path).unlink(missing_ok=True)
