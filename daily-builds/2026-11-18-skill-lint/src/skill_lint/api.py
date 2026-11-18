"""FastAPI server for skill-lint."""

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .linter import lint_text
from .models import Report

app = FastAPI(
    title="skill-lint",
    description="Offline linter and quality scorer for agent SKILL.md files",
    version="0.1.0",
)


class LintRequest(BaseModel):
    """Request body for /lint endpoint."""

    content: str
    filename: str = "skill.md"


class LintResponse(BaseModel):
    """Response from /lint endpoint."""

    report: dict[str, Any]


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/rules")
async def get_rules() -> dict[str, list[dict[str, str]]]:
    """Get list of all linting rules."""
    rules = [
        {"id": "SL001", "description": "Missing or invalid frontmatter"},
        {"id": "SL002", "description": "Name not kebab-case or doesn't match directory"},
        {"id": "SL003", "description": "Description length invalid"},
        {"id": "SL004", "description": "Description lacks trigger phrase"},
        {"id": "SL005", "description": "Body too long"},
        {"id": "SL006", "description": "Referenced file doesn't exist"},
        {"id": "SL007", "description": "Broken heading hierarchy"},
        {"id": "SL008", "description": "High filler phrase density"},
        {"id": "SL009", "description": "No concrete examples"},
        {"id": "SL010", "description": "Possible secrets detected"},
        {"id": "SL011", "description": "Duplicate skill name"},
    ]
    return {"rules": rules}


@app.post("/lint")
async def lint_endpoint(request: LintRequest) -> dict[str, Any]:
    """Lint a SKILL.md file content.
    
    Args:
        request: Lint request with content
        
    Returns:
        Linting report
    """
    try:
        report: Report = lint_text(request.content, filename=request.filename)
        return report.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
