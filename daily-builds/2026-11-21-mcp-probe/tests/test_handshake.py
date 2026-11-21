"""Tests for handshake rules."""

import pytest
from mcp_probe.models import JsonRpcResponse, Severity
from mcp_probe.rules.handshake import check_handshake


def test_handshake_valid():
    """Test valid handshake produces no errors."""
    init_response = JsonRpcResponse(
        jsonrpc="2.0",
        id=1,
        result={
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "test", "version": "1.0"}
        }
    )
    
    unknown_response = JsonRpcResponse(
        jsonrpc="2.0",
        id=2,
        error={"code": -32601, "message": "Method not found"}
    )
    
    ping_response = JsonRpcResponse(
        jsonrpc="2.0",
        id=3,
        result={}
    )
    
    findings = check_handshake(init_response, 1, unknown_response, True, ping_response, 3)
    
    errors = [f for f in findings if f.severity == Severity.ERROR]
    assert len(errors) == 0


def test_handshake_missing_protocol_version():
    """Test missing protocolVersion is detected."""
    init_response = JsonRpcResponse(
        jsonrpc="2.0",
        id=1,
        result={
            "capabilities": {},
            "serverInfo": {"name": "test", "version": "1.0"}
        }
    )
    
    unknown_response = JsonRpcResponse(
        jsonrpc="2.0",
        id=2,
        error={"code": -32601, "message": "Method not found"}
    )
    
    ping_response = JsonRpcResponse(jsonrpc="2.0", id=3, result={})
    
    findings = check_handshake(init_response, 1, unknown_response, True, ping_response, 3)
    
    assert any(f.rule_id == "HS004" for f in findings)


def test_handshake_missing_server_info():
    """Test missing serverInfo is detected."""
    init_response = JsonRpcResponse(
        jsonrpc="2.0",
        id=1,
        result={
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        }
    )
    
    unknown_response = JsonRpcResponse(
        jsonrpc="2.0",
        id=2,
        error={"code": -32601, "message": "Method not found"}
    )
    
    ping_response = JsonRpcResponse(jsonrpc="2.0", id=3, result={})
    
    findings = check_handshake(init_response, 1, unknown_response, True, ping_response, 3)
    
    assert any(f.rule_id == "HS006" for f in findings)


def test_handshake_id_mismatch():
    """Test response ID mismatch is detected."""
    init_response = JsonRpcResponse(
        jsonrpc="2.0",
        id=999,
        result={
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "serverInfo": {"name": "test", "version": "1.0"}
        }
    )
    
    unknown_response = JsonRpcResponse(
        jsonrpc="2.0",
        id=2,
        error={"code": -32601, "message": "Method not found"}
    )
    
    ping_response = JsonRpcResponse(jsonrpc="2.0", id=3, result={})
    
    findings = check_handshake(init_response, 1, unknown_response, True, ping_response, 3)
    
    assert any(f.rule_id == "HS002" for f in findings)


def test_handshake_wrong_error_code():
    """Test wrong error code for unknown method."""
    init_response = JsonRpcResponse(
        jsonrpc="2.0",
        id=1,
        result={
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "serverInfo": {"name": "test", "version": "1.0"}
        }
    )
    
    unknown_response = JsonRpcResponse(
        jsonrpc="2.0",
        id=2,
        error={"code": -32000, "message": "Wrong code"}
    )
    
    ping_response = JsonRpcResponse(jsonrpc="2.0", id=3, result={})
    
    findings = check_handshake(init_response, 1, unknown_response, True, ping_response, 3)
    
    assert any(f.rule_id == "HS009" for f in findings)


def test_handshake_malformed_json_crash():
    """Test server crash on malformed JSON is detected."""
    init_response = JsonRpcResponse(
        jsonrpc="2.0",
        id=1,
        result={
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "serverInfo": {"name": "test", "version": "1.0"}
        }
    )
    
    unknown_response = JsonRpcResponse(
        jsonrpc="2.0",
        id=2,
        error={"code": -32601, "message": "Method not found"}
    )
    
    ping_response = JsonRpcResponse(jsonrpc="2.0", id=3, result={})
    
    findings = check_handshake(init_response, 1, unknown_response, False, ping_response, 3)
    
    assert any(f.rule_id == "HS011" for f in findings)
