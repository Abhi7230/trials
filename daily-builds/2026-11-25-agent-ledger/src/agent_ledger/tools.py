"""MCP-style tool manifest generation."""

from typing import Any


def generate_tool_manifest() -> list[dict[str, Any]]:
    """Generate MCP-style tool definitions."""
    return [
        {
            "name": "send_money",
            "description": "Send money from one wallet to another. Subject to policy approval.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "from": {
                        "type": "string",
                        "description": "Source wallet ID",
                    },
                    "to": {
                        "type": "string",
                        "description": "Destination wallet ID",
                    },
                    "amount_cents": {
                        "type": "integer",
                        "description": "Amount in cents",
                        "minimum": 1,
                    },
                    "memo": {
                        "type": "string",
                        "description": "Optional memo",
                        "default": "",
                    },
                },
                "required": ["from", "to", "amount_cents"],
            },
        },
        {
            "name": "request_money",
            "description": "Request money from another wallet.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "from": {
                        "type": "string",
                        "description": "Wallet to request from",
                    },
                    "to": {
                        "type": "string",
                        "description": "Your wallet ID",
                    },
                    "amount_cents": {
                        "type": "integer",
                        "description": "Amount in cents",
                        "minimum": 1,
                    },
                    "memo": {
                        "type": "string",
                        "description": "Optional memo",
                        "default": "",
                    },
                },
                "required": ["from", "to", "amount_cents"],
            },
        },
        {
            "name": "split_bill",
            "description": "Split a bill among participants with tax and tip.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "payer": {
                        "type": "string",
                        "description": "Wallet ID of payer",
                    },
                    "participants": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of participant wallet IDs",
                    },
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "owner": {
                                    "type": "string",
                                    "description": "Wallet ID of owner, or null for shared",
                                },
                                "amount_cents": {
                                    "type": "integer",
                                    "minimum": 1,
                                },
                            },
                            "required": ["amount_cents"],
                        },
                        "description": "Bill items",
                    },
                    "tax_rate": {
                        "type": "number",
                        "description": "Tax rate (e.g., 0.08875 for 8.875%)",
                        "default": 0.0,
                    },
                    "tip_rate": {
                        "type": "number",
                        "description": "Tip rate (e.g., 0.20 for 20%)",
                        "default": 0.0,
                    },
                },
                "required": ["payer", "participants", "items"],
            },
        },
        {
            "name": "get_balance",
            "description": "Get wallet balance and spending information.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "wallet_id": {
                        "type": "string",
                        "description": "Wallet ID",
                    },
                },
                "required": ["wallet_id"],
            },
        },
        {
            "name": "list_transactions",
            "description": "List recent transactions for a wallet.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "wallet_id": {
                        "type": "string",
                        "description": "Wallet ID",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of transactions",
                        "default": 50,
                    },
                },
                "required": ["wallet_id"],
            },
        },
    ]
