"""Property-based tests."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule, precondition

from agent_ledger.app import create_app
from agent_ledger.clock import FixedClock
from datetime import datetime, timezone


@given(
    deposits=st.lists(st.integers(min_value=1, max_value=10000), min_size=1, max_size=10),
    transfers=st.lists(st.integers(min_value=1, max_value=1000), min_size=0, max_size=20),
)
@settings(max_examples=200, derandomize=True)
def test_balance_never_negative(deposits, transfers):
    """Property test: balance never goes negative."""
    import tempfile
    from fastapi.testclient import TestClient
    
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        clock = FixedClock(datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc))
        app = create_app(db_path=f.name, clock=clock)
        client = TestClient(app)
        
        # Create wallets
        client.post("/v1/wallets", json={"id": "alice"})
        client.post("/v1/wallets", json={"id": "bob"})
        
        # Set policy for auto-approval
        client.put(
            "/v1/wallets/alice/policy",
            json={"trusted_contacts": ["bob"], "auto_approve_limit_cents": 10**9},
        )
        
        # Deposits
        total_deposited = 0
        for i, amount in enumerate(deposits):
            client.post(
                "/v1/wallets/alice/deposits",
                json={"amount_cents": amount},
                headers={"Idempotency-Key": f"d-{i}"},
            )
            total_deposited += amount
        
        # Transfers
        for i, amount in enumerate(transfers):
            client.post(
                "/v1/transfers",
                json={"from": "alice", "to": "bob", "amount_cents": amount},
                headers={"Idempotency-Key": f"tx-{i}"},
            )
        
        # Check invariants
        response = client.get("/v1/admin/invariants")
        assert response.json()["ok"] is True
        
        # Check balances are non-negative
        response = client.get("/v1/wallets/alice")
        alice_balance = response.json()["balance"]
        assert alice_balance >= 0
        
        response = client.get("/v1/wallets/bob")
        bob_balance = response.json()["balance"]
        assert bob_balance >= 0
        
        # Check sum equals deposits
        assert alice_balance + bob_balance == total_deposited
