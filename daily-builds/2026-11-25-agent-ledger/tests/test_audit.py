"""Tests for audit log."""

import pytest


def test_audit_log_records_attempts(client):
    """Test audit log records all attempts."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Successful transfer
    client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 1000},
        headers={"Idempotency-Key": "tx1"},
    )
    
    # Rejected transfer
    client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 10**9},
        headers={"Idempotency-Key": "tx2"},
    )
    
    # Get audit log
    response = client.get("/v1/audit?wallet=alice")
    assert response.status_code == 200
    
    entries = response.json()
    assert len(entries) >= 2
    
    # Check that both attempts are logged
    decisions = [e["decision"] for e in entries]
    assert "completed" in decisions
    assert "rejected" in decisions


def test_audit_log_includes_rejected_attempts(client):
    """Test rejected attempts are audited."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 1000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # This will be rejected due to insufficient funds
    client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 10000},
        headers={"Idempotency-Key": "tx1"},
    )
    
    response = client.get("/v1/audit")
    entries = response.json()
    
    rejected = [e for e in entries if e["decision"] == "rejected"]
    assert len(rejected) >= 1


def test_audit_survives_rollback(client, app):
    """Test audit entry is written even when transaction rolls back."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 1000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # This will fail
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 10000},
        headers={"Idempotency-Key": "tx1"},
    )
    assert response.status_code == 409
    
    # Check audit log has the failed attempt
    response = client.get("/v1/audit?wallet=alice")
    entries = response.json()
    assert len(entries) >= 1
