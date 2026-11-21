"""Transcript recording and replay."""

import json
from typing import Any
from pathlib import Path


class TranscriptRecorder:
    """Record MCP session to JSONL."""
    
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.handle = None
    
    def start(self) -> None:
        """Start recording."""
        self.handle = self.output_path.open("w")
    
    def record_request(self, request: dict[str, Any]) -> None:
        """Record a request."""
        if self.handle:
            self.handle.write(json.dumps({"type": "request", "data": request}) + "\n")
            self.handle.flush()
    
    def record_response(self, response: dict[str, Any]) -> None:
        """Record a response."""
        if self.handle:
            self.handle.write(json.dumps({"type": "response", "data": response}) + "\n")
            self.handle.flush()
    
    def stop(self) -> None:
        """Stop recording."""
        if self.handle:
            self.handle.close()
            self.handle = None


def load_transcript(path: str) -> list[dict[str, Any]]:
    """Load a transcript from JSONL file."""
    transcript = []
    with open(path, "r") as f:
        for line in f:
            if line.strip():
                transcript.append(json.loads(line))
    return transcript


def check_transcript_static(transcript_path: str) -> dict[str, Any]:
    """Run static checks on a recorded transcript."""
    from .models import Finding, Report, ToolInfo
    from .rules import check_tool_schemas
    
    transcript = load_transcript(transcript_path)
    findings = []
    tools = []
    
    for entry in transcript:
        if entry.get("type") == "response":
            data = entry.get("data", {})
            result = data.get("result", {})
            
            if "tools" in result:
                for tool_data in result["tools"]:
                    try:
                        tools.append(ToolInfo(**tool_data))
                    except Exception:
                        pass
    
    if tools:
        schema_findings = check_tool_schemas(tools)
        findings.extend(schema_findings)
    
    from .scoring import calculate_score
    score, grade = calculate_score(findings)
    
    return Report(
        findings=findings,
        score=score,
        grade=grade,
        stats={"tool_count": len(tools), "source": "transcript"},
    ).model_dump()
