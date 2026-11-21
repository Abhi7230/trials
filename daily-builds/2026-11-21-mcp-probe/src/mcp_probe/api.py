"""FastAPI endpoint for transcript checking."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .transcript import check_transcript_static
from .models import Report

app = FastAPI(title="MCP Probe API", version="0.1.0")


class TranscriptCheckRequest(BaseModel):
    """Request body for transcript checking."""
    transcript: str


class RuleInfo(BaseModel):
    """Rule information."""
    rule_ids: str
    category: str
    description: str


@app.post("/check-transcript")
async def check_transcript_endpoint(request: TranscriptCheckRequest) -> dict:
    """Check a transcript provided as JSONL text."""
    import tempfile
    from pathlib import Path
    
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(request.transcript)
            temp_path = f.name
        
        report_dict = check_transcript_static(temp_path)
        
        Path(temp_path).unlink()
        
        return report_dict
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/rules")
async def get_rules() -> list[RuleInfo]:
    """List all probe rules."""
    return [
        RuleInfo(rule_ids="HS001-HS013", category="Handshake", description="Protocol handshake conformance"),
        RuleInfo(rule_ids="TS001-TS011", category="Tool Schema", description="Tool schema validation"),
        RuleInfo(rule_ids="RS001-RS007", category="Results", description="Tool result conformance"),
        RuleInfo(rule_ids="FZ001-FZ003", category="Fuzzing", description="Invalid input handling"),
        RuleInfo(rule_ids="RB001-RB005", category="Robustness", description="Server stability and performance"),
    ]


@app.get("/")
async def root():
    """API root."""
    return {"name": "MCP Probe API", "version": "0.1.0"}
