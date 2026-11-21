#!/usr/bin/env python3
"""A well-behaved MCP server for testing."""

import sys
import json


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
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "good-server",
                "version": "1.0.0"
            }
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
                    "name": "echo",
                    "description": "Echoes back the input message provided by the user",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The message to echo back"
                            }
                        },
                        "required": ["message"]
                    }
                },
                {
                    "name": "add",
                    "description": "Adds two numbers together and returns the sum",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "a": {
                                "type": "integer",
                                "description": "First number to add"
                            },
                            "b": {
                                "type": "integer",
                                "description": "Second number to add"
                            }
                        },
                        "required": ["a", "b"]
                    }
                }
            ]
        }
    })


def handle_tools_call(request_id, params):
    """Handle tools/call request."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if tool_name == "echo":
        if "message" not in arguments:
            send_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": "Missing required field: message"}]
                }
            })
        else:
            send_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": arguments["message"]}]
                }
            })
    elif tool_name == "add":
        if "a" not in arguments or "b" not in arguments:
            send_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": "Missing required fields"}]
                }
            })
        else:
            try:
                result = int(arguments["a"]) + int(arguments["b"])
                send_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": str(result)}]
                    }
                })
            except (ValueError, TypeError):
                send_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "isError": True,
                        "content": [{"type": "text", "text": "Invalid number format"}]
                    }
                })
    else:
        send_response({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": "Tool not found"}
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
