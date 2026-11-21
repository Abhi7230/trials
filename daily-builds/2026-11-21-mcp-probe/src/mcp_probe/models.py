"""Data models for MCP probe."""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Finding severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Finding(BaseModel):
    """A single conformance or robustness finding."""
    rule_id: str
    severity: Severity
    message: str
    location: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class Report(BaseModel):
    """Complete probe report."""
    findings: list[Finding] = Field(default_factory=list)
    score: float = 100.0
    grade: str = "A"
    stats: dict[str, Any] = Field(default_factory=dict)
    server_info: Optional[dict[str, Any]] = None


class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 request."""
    jsonrpc: str = "2.0"
    id: Optional[int | str] = None
    method: str
    params: Optional[dict[str, Any]] = None


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 response."""
    jsonrpc: str
    id: Optional[int | str] = None
    result: Optional[Any] = None
    error: Optional[dict[str, Any]] = None


class ToolInfo(BaseModel):
    """Tool information from tools/list."""
    name: str
    description: str
    inputSchema: dict[str, Any]


class ServerCapabilities(BaseModel):
    """MCP server capabilities."""
    tools: Optional[dict[str, Any]] = None
    resources: Optional[dict[str, Any]] = None
    prompts: Optional[dict[str, Any]] = None


class ServerInfo(BaseModel):
    """MCP server info."""
    name: str
    version: str


class InitializeResult(BaseModel):
    """Result of initialize call."""
    protocolVersion: str
    capabilities: ServerCapabilities
    serverInfo: ServerInfo
