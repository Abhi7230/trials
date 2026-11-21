#!/usr/bin/env python3
"""A buggy MCP server for testing error detection."""

import sys
import json


def send_response(response):
    """Send JSON-RPC response."""
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def handle_initialize(request_id, params):
    """Handle initialize with missing fields."""
    send_response({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "buggy-server"
            }
        }
    })


def handle_tools_list(request_id, params):
    """Handle tools/list with schema problems."""
    sys.stderr.write("Loading tools...\n")
    
    send_response({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "tools": [
                {
                    "name": "bad name with spaces",
                    "description": "short",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"}
                        },
                        "required": ["missing_field"]
                    }
                },
                {
                    "name": "crash_tool",
                    "description": "This tool crashes on invalid input instead of returning error",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": "integer",
                                "description": "An integer value",
                                "enum": []
                            }
                        },
                        "required": ["value"]
                    }
                },
                {
                    "name": "duplicate",
                    "description": "First duplicate tool entry in the list",
                    "inputSchema": {"type": "object"}
                },
                {
                    "name": "duplicate",
                    "description": "Second duplicate tool entry with same name",
                    "inputSchema": {"type": "object"}
                }
            ]
        }
    })


def handle_tools_call(request_id, params):
    """Handle tools/call with bad behavior."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if tool_name == "crash_tool":
        if "value" not in arguments or not isinstance(arguments.get("value"), int):
            sys.exit(1)
        
        send_response({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": "ok"}]
            }
        })
    else:
        send_response({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": "should be a list not a string"
            }
        })


def handle_ping(request_id, params):
    """Handle ping with wrong id."""
    send_response({
        "jsonrpc": "2.0",
        "id": 9999,
        "result": {}
    })


def main():
    """Main event loop."""
    sys.stdout.write("Starting buggy server (this is stdout noise)\n")
    sys.stdout.flush()
    
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
                    "result": {"status": "ok"}
                })


if __name__ == "__main__":
    main()
