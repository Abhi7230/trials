"""Pytest fixtures."""

import tempfile
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from agent_ledger.app import create_app
from agent_ledger.clock import FixedClock
from agent_ledger.db import get_connection


@pytest.fixture
def clock():
    """Fixed clock for testing."""
    return FixedClock(datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc))


@pytest.fixture
def secret():
    """Fixed secret for testing."""
    return b"test-secret-key-for-testing-only"


@pytest.fixture
def db_path():
    """Temporary database file."""
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    yield f.name


@pytest.fixture
def app(db_path, clock, secret):
    """FastAPI application with test database."""
    return create_app(db_path=db_path, clock=clock, secret=secret)


@pytest.fixture
def client(app):
    """HTTP client for testing."""
    with TestClient(app) as c:
        yield c
        # Check invariants after test
        if hasattr(app.state, "invariants"):
            checker = app.state.invariants
            result = checker.check_all()
            assert result["ok"], f"Invariants failed: {result['violations']}"


@pytest.fixture
def conn(db_path):
    """Database connection for direct testing."""
    from agent_ledger.db import init_db
    c = get_connection(db_path)
    init_db(c)
    yield c
    c.close()
