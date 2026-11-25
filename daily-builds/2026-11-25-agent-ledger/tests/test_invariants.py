"""Tests for invariant checker."""

import pytest


def test_invariants_pass_on_clean_db(client):
    """Test invariants pass on clean database."""
    response = client.get("/v1/admin/invariants")
    assert response.status_code == 200
    result = response.json()
    assert result["ok"] is True
    assert len(result["violations"]) == 0


def test_invariants_pass_after_transfers(client):
    """Test invariants pass after normal operations."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 5000},
        headers={"Idempotency-Key": "tx1"},
    )
    
    response = client.get("/v1/admin/invariants")
    assert response.json()["ok"] is True


def test_corruption_detection(client, app, request):
    """Test detection of corrupted ledger."""
    # Mark this test to skip invariant checking in teardown
    request.node.skip_invariants = True
    
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 5000},
        headers={"Idempotency-Key": "tx1"},
    )
    
    # Corrupt database by deleting a posting
    conn = app.state.conn
    cursor = conn.cursor()
    cursor.execute("DELETE FROM postings WHERE id = (SELECT MIN(id) FROM postings)")
    conn.commit()
    
    # Check invariants
    response = client.get("/v1/admin/invariants")
    result = response.json()
    
    assert result["ok"] is False
    assert len(result["violations"]) > 0
    
    # Should detect unbalanced entry and balance mismatch
    violation_types = {v["type"] for v in result["violations"]}
    assert "unbalanced_entry" in violation_types or "balance_mismatch" in violation_types


def test_negative_balance_detection(client, app, request):
    """Test detection of negative balance."""
    # Mark this test to skip invariant checking in teardown
    request.node.skip_invariants = True
    
    client.post("/v1/wallets", json={"id": "alice"})
    
    # Corrupt by setting negative balance
    conn = app.state.conn
    cursor = conn.cursor()
    cursor.execute("UPDATE wallets SET balance = -1000 WHERE id = 'alice'")
    conn.commit()
    
    response = client.get("/v1/admin/invariants")
    result = response.json()
    
    assert result["ok"] is False
    violations = [v for v in result["violations"] if v["type"] == "negative_balance"]
    assert len(violations) > 0


def test_amount_validation(client):
    """Test amount validation."""
    client.post("/v1/wallets", json={"id": "alice"})
    
    # Amount 0
    response = client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 0},
        headers={"Idempotency-Key": "d1"},
    )
    assert response.status_code == 422
    
    # Negative
    response = client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": -100},
        headers={"Idempotency-Key": "d2"},
    )
    assert response.status_code == 422
    
    # Too large (> 10^12)
    response = client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10**12 + 1},
        headers={"Idempotency-Key": "d3"},
    )
    assert response.status_code == 422
    
    # 10^12 is accepted
    response = client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10**12},
        headers={"Idempotency-Key": "d4"},
    )
    assert response.status_code == 201
