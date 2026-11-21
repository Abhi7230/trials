#!/usr/bin/env python3
"""A slow MCP server for timeout testing."""

import sys
import json
import time


def send_response(response):
    """Send JSON-RPC response."""
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def handle_initialize(request_id, params):
    """Handle initialize request."""
    send_response({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "slow-server", "version": "1.0.0"}
        }
    })


def handle_tools_list(request_id, params):
    """Handle tools/list request."""
    send_response({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "tools": [
                {
                    "name": "slow_operation",
                    "description": "An operation that takes a very long time to complete",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "data": {"type": "string", "description": "Input data"}
                        }
                    }
                }
            ]
        }
    })


def handle_tools_call(request_id, params):
    """Handle tools/call with long delay."""
    time.sleep(10)
    send_response({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"content": [{"type": "text", "text": "done"}]}
    })


def handle_ping(request_id, params):
    """Handle ping request."""
    send_response({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {}
    })


def main():
    """Main event loop."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})
        
        if method == "initialize":
            handle_initialize(request_id, params)
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            handle_tools_list(request_id, params)
        elif method == "tools/call":
            handle_tools_call(request_id, params)
        elif method == "ping":
            handle_ping(request_id, params)
        else:
            if request_id is not None:
                send_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": "Method not found"}
                })


if __name__ == "__main__":
    main()
