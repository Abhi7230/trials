"""Tests for CLI."""

import pytest
import sys
from pathlib import Path
from typer.testing import CliRunner
from mcp_probe.cli import app

runner = CliRunner()
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_cli_run_good_server():
    """Test running against good server."""
    result = runner.invoke(app, [
        "run",
        "--cmd", f"{sys.executable} {FIXTURES_DIR / 'good_server.py'}",
        "--timeout", "5",
        "--fuzz-per-tool", "4"
    ])
    
    assert result.exit_code == 0
    assert "MCP Probe Report" in result.stdout


def test_cli_run_with_fail_under_pass():
    """Test --fail-under passes when score is high."""
    result = runner.invoke(app, [
        "run",
        "--cmd", f"{sys.executable} {FIXTURES_DIR / 'good_server.py'}",
        "--timeout", "5",
        "--fuzz-per-tool", "2",
        "--fail-under", "50"
    ])
    
    assert result.exit_code == 0


def test_cli_run_with_fail_under_fail():
    """Test --fail-under fails when score is low."""
    result = runner.invoke(app, [
        "run",
        "--cmd", f"{sys.executable} {FIXTURES_DIR / 'buggy_server.py'}",
        "--timeout", "2",
        "--fuzz-per-tool", "2",
        "--fail-under", "90"
    ])
    
    assert result.exit_code == 1


def test_cli_run_json_format():
    """Test JSON output format."""
    result = runner.invoke(app, [
        "run",
        "--cmd", f"{sys.executable} {FIXTURES_DIR / 'good_server.py'}",
        "--timeout", "5",
        "--fuzz-per-tool", "2",
        "--format", "json"
    ])
    
    assert result.exit_code == 0
    assert '"score"' in result.stdout
    assert '"grade"' in result.stdout


def test_cli_run_markdown_format():
    """Test Markdown output format."""
    result = runner.invoke(app, [
        "run",
        "--cmd", f"{sys.executable} {FIXTURES_DIR / 'good_server.py'}",
        "--timeout", "5",
        "--fuzz-per-tool", "2",
        "--format", "markdown"
    ])
    
    assert result.exit_code == 0
    assert "# MCP Probe Report" in result.stdout


def test_cli_rules():
    """Test rules command."""
    result = runner.invoke(app, ["rules"])
    
    assert result.exit_code == 0
    assert "Handshake" in result.stdout
    assert "Tool Schema" in result.stdout
    assert "Robustness" in result.stdout
