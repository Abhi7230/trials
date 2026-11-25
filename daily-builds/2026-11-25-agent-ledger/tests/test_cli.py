"""Tests for CLI."""

import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest
import uvicorn
from typer.testing import CliRunner

from agent_ledger.cli import app as cli_app


runner = CliRunner()


def test_check_command_clean_db(tmp_path):
    """Test check command on clean database."""
    db_path = tmp_path / "test.db"
    
    # Initialize database
    from agent_ledger.db import get_connection, init_db
    conn = get_connection(str(db_path))
    init_db(conn)
    conn.close()
    
    result = runner.invoke(cli_app, ["check", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "All invariants passed" in result.stdout


def test_check_command_corrupted_db(tmp_path):
    """Test check command on corrupted database."""
    db_path = tmp_path / "test.db"
    
    # Create and corrupt database
    from agent_ledger.db import get_connection, init_db
    conn = get_connection(str(db_path))
    init_db(conn)
    
    # Add wallet and corrupt it
    from agent_ledger.ledger import Ledger
    from agent_ledger.clock import FixedClock
    from datetime import datetime, timezone
    
    clock = FixedClock()
    ledger = Ledger(conn)
    ledger.create_wallet("test", "USD", clock.now())
    
    # Corrupt by setting negative balance
    cursor = conn.cursor()
    cursor.execute("UPDATE wallets SET balance = -1000 WHERE id = 'test'")
    conn.commit()
    conn.close()
    
    result = runner.invoke(cli_app, ["check", "--db", str(db_path)])
    assert result.exit_code == 1
    assert "violations" in result.stdout.lower()


def test_tools_command():
    """Test tools command."""
    result = runner.invoke(cli_app, ["tools"])
    assert result.exit_code == 0
    
    # Should output valid JSON
    output = json.loads(result.stdout)
    assert isinstance(output, list)
    assert len(output) == 5


def test_replay_command():
    """Test replay command."""
    result = runner.invoke(cli_app, ["replay", "examples/dinner.yaml", "--format", "json"])
    # Should complete without crashing
    assert result.exit_code in [0, 1]


def test_serve_command():
    """Test serve command."""
    with patch.object(uvicorn, 'run') as mock_run:
        result = runner.invoke(cli_app, ["serve", "--db", "test.db", "--port", "9000"])
        
        # Should call uvicorn.run
        assert mock_run.called
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["port"] == 9000
        assert call_kwargs["host"] == "127.0.0.1"
