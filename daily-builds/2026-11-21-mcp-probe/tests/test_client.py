"""Tests for JSON-RPC client."""

import pytest
import sys
from pathlib import Path
from mcp_probe.client import McpClient


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_client_start_stop():
    """Test client can start and stop server."""
    client = McpClient(f"{sys.executable} {FIXTURES_DIR / 'good_server.py'}")
    client.start()
    assert client.is_alive()
    client.stop()
    assert not client.is_alive()


def test_client_context_manager():
    """Test client works as context manager."""
    with McpClient(f"{sys.executable} {FIXTURES_DIR / 'good_server.py'}") as client:
        assert client.is_alive()
    assert not client.is_alive()


def test_client_send_request():
    """Test sending a request."""
    with McpClient(f"{sys.executable} {FIXTURES_DIR / 'good_server.py'}") as client:
        response = client.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        })
        assert response.jsonrpc == "2.0"
        assert response.id == 1
        assert response.result is not None


@pytest.mark.skip(reason="Timeout test can hang, tested in integration")
def test_client_timeout():
    """Test request timeout."""
    with McpClient(f"{sys.executable} {FIXTURES_DIR / 'slow_server.py'}", timeout=1.0) as client:
        client.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        })
        client.send_notification("notifications/initialized")
        
        with pytest.raises(TimeoutError):
            client.send_request("tools/call", {"name": "slow_operation", "arguments": {"data": "test"}})


def test_client_notification():
    """Test sending notification."""
    with McpClient(f"{sys.executable} {FIXTURES_DIR / 'good_server.py'}") as client:
        client.send_notification("notifications/initialized")


def test_client_detects_stdout_noise():
    """Test client detects non-JSON stdout."""
    with McpClient(f"{sys.executable} {FIXTURES_DIR / 'buggy_server.py'}") as client:
        client.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        })
        assert len(client.stdout_noise) > 0
