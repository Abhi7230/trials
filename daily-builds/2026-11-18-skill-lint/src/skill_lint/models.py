"""Core data models for skill-lint."""

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Severity(StrEnum):
    """Finding severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Finding(BaseModel):
    """A single linting finding."""

    rule_id: str
    severity: Severity
    message: str
    line: int | None = None
    column: int | None = None
    end_line: int | None = None
    fix: str | None = None


class Skill(BaseModel):
    """Parsed SKILL.md file."""

    path: Path
    name: str | None = None
    description: str | None = None
    body: str
    frontmatter: dict[str, Any] = Field(default_factory=dict)
    lines: list[str] = Field(default_factory=list)
    referenced_files: list[str] = Field(default_factory=list)


class Score(BaseModel):
    """Quality score for a skill."""

    value: int = Field(ge=0, le=100)
    grade: str
    findings_count: int
    errors: int
    warnings: int
    info: int


class Report(BaseModel):
    """Complete linting report."""

    skills: list[Skill]
    findings: dict[str, list[Finding]] = Field(default_factory=dict)
    scores: dict[str, Score] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)
