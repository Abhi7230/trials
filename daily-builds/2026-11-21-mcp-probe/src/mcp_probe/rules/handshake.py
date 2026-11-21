"""Handshake conformance rules (HS001...)."""

import json
from typing import Any
from ..models import Finding, Severity, JsonRpcResponse


def check_handshake(
    initialize_response: JsonRpcResponse,
    initialize_request_id: int,
    unknown_method_response: JsonRpcResponse,
    malformed_json_ok: bool,
    ping_response: JsonRpcResponse,
    ping_request_id: int,
) -> list[Finding]:
    """Check MCP handshake conformance."""
    findings = []
    
    if initialize_response.jsonrpc != "2.0":
        findings.append(Finding(
            rule_id="HS001",
            severity=Severity.ERROR,
            message=f"initialize response jsonrpc must be '2.0', got '{initialize_response.jsonrpc}'"
        ))
    
    if initialize_response.id != initialize_request_id:
        findings.append(Finding(
            rule_id="HS002",
            severity=Severity.ERROR,
            message=f"initialize response id mismatch: expected {initialize_request_id}, got {initialize_response.id}"
        ))
    
    if initialize_response.error:
        findings.append(Finding(
            rule_id="HS003",
            severity=Severity.ERROR,
            message=f"initialize returned error: {initialize_response.error}"
        ))
    elif initialize_response.result:
        result = initialize_response.result
        
        if "protocolVersion" not in result:
            findings.append(Finding(
                rule_id="HS004",
                severity=Severity.ERROR,
                message="initialize result missing protocolVersion"
            ))
        
        if "capabilities" not in result:
            findings.append(Finding(
                rule_id="HS005",
                severity=Severity.ERROR,
                message="initialize result missing capabilities"
            ))
        
        if "serverInfo" not in result:
            findings.append(Finding(
                rule_id="HS006",
                severity=Severity.ERROR,
                message="initialize result missing serverInfo"
            ))
        elif result.get("serverInfo"):
            server_info = result["serverInfo"]
            if "name" not in server_info:
                findings.append(Finding(
                    rule_id="HS007",
                    severity=Severity.ERROR,
                    message="serverInfo missing name"
                ))
            if "version" not in server_info:
                findings.append(Finding(
                    rule_id="HS008",
                    severity=Severity.ERROR,
                    message="serverInfo missing version"
                ))
    
    if unknown_method_response.error:
        error_code = unknown_method_response.error.get("code")
        if error_code != -32601:
            findings.append(Finding(
                rule_id="HS009",
                severity=Severity.ERROR,
                message=f"unknown method should return error code -32601, got {error_code}"
            ))
    else:
        findings.append(Finding(
            rule_id="HS010",
            severity=Severity.ERROR,
            message="unknown method should return error, got result instead"
        ))
    
    if not malformed_json_ok:
        findings.append(Finding(
            rule_id="HS011",
            severity=Severity.ERROR,
            message="server crashed or hung on malformed JSON"
        ))
    
    if ping_response.jsonrpc != "2.0":
        findings.append(Finding(
            rule_id="HS012",
            severity=Severity.ERROR,
            message=f"ping response jsonrpc must be '2.0', got '{ping_response.jsonrpc}'"
        ))
    
    if ping_response.id != ping_request_id:
        findings.append(Finding(
            rule_id="HS013",
            severity=Severity.ERROR,
            message=f"ping response id mismatch: expected {ping_request_id}, got {ping_response.id}"
        ))
    
    return findings
