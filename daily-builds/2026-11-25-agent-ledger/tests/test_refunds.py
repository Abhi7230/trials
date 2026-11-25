"""Tests for refunds and reversals."""

import pytest


def test_partial_refunds(client):
    """Test partial refunds from spec."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Set policy to auto-approve
    client.put(
        "/v1/wallets/alice/policy",
        json={"trusted_contacts": ["bob"], "auto_approve_limit_cents": 10000},
    )
    
    # Create transfer (should auto-complete)
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 5000},
        headers={"Idempotency-Key": "tx1"},
    )
    transfer_id = response.json()["id"]
    assert response.json()["status"] == "completed", f"Transfer should be completed, got {response.json()['status']}"
    
    # Refund 3000 - ok
    response = client.post(
        f"/v1/transfers/{transfer_id}/refunds",
        json={"amount_cents": 3000},
    )
    assert response.status_code == 200
    
    # Check balances
    response = client.get("/v1/wallets/alice")
    assert response.json()["balance"] == 8000
    
    response = client.get("/v1/wallets/bob")
    assert response.json()["balance"] == 2000
    
    # Refund 2500 - exceeds remaining (2000)
    response = client.post(
        f"/v1/transfers/{transfer_id}/refunds",
        json={"amount_cents": 2500},
    )
    assert response.status_code == 409
    assert response.json()["error"]["reason"] == "exceeds_refundable"
    
    # Refund 2000 - ok
    response = client.post(
        f"/v1/transfers/{transfer_id}/refunds",
        json={"amount_cents": 2000},
    )
    assert response.status_code == 200
    
    # Refund 1 - fully refunded
    response = client.post(
        f"/v1/transfers/{transfer_id}/refunds",
        json={"amount_cents": 1},
    )
    assert response.status_code == 409
    assert response.json()["error"]["reason"] == "fully_refunded"


def test_full_reverse_after_partial_refund(client):
    """Test full reversal rejected after partial refund."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Set policy to auto-approve
    client.put(
        "/v1/wallets/alice/policy",
        json={"trusted_contacts": ["bob"], "auto_approve_limit_cents": 10000},
    )
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 5000},
        headers={"Idempotency-Key": "tx1"},
    )
    transfer_id = response.json()["id"]
    assert response.json()["status"] == "completed"
    
    # Partial refund
    client.post(
        f"/v1/transfers/{transfer_id}/refunds",
        json={"amount_cents": 1000},
    )
    
    # Try full reverse
    response = client.post(f"/v1/transfers/{transfer_id}/reverse")
    assert response.status_code == 409
    assert response.json()["error"]["reason"] == "partially_refunded"


def test_reversal_window(client, clock):
    """Test reversal window."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Set policy to auto-approve
    client.put(
        "/v1/wallets/alice/policy",
        json={"trusted_contacts": ["bob"], "auto_approve_limit_cents": 10000},
    )
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 5000},
        headers={"Idempotency-Key": "tx1"},
    )
    transfer_id = response.json()["id"]
    assert response.json()["status"] == "completed"
    
    # Advance exactly 72 hours - should still work
    clock.advance(hours=72)
    
    response = client.post(f"/v1/transfers/{transfer_id}/reverse")
    assert response.status_code == 200
    
    # Create another transfer
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 3000},
        headers={"Idempotency-Key": "tx2"},
    )
    transfer_id_2 = response.json()["id"]
    
    # Advance 72h + 1s - should fail
    clock.advance(hours=72, seconds=1)
    
    response = client.post(f"/v1/transfers/{transfer_id_2}/reverse")
    assert response.status_code == 409
    assert response.json()["error"]["reason"] == "reversal_window_closed"


def test_double_reversal(client):
    """Test double reversal rejected."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Set policy to auto-approve
    client.put(
        "/v1/wallets/alice/policy",
        json={"trusted_contacts": ["bob"], "auto_approve_limit_cents": 10000},
    )
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 5000},
        headers={"Idempotency-Key": "tx1"},
    )
    transfer_id = response.json()["id"]
    assert response.json()["status"] == "completed"
    
    # First reversal - ok
    response = client.post(f"/v1/transfers/{transfer_id}/reverse")
    assert response.status_code == 200
    
    # Second reversal - rejected
    response = client.post(f"/v1/transfers/{transfer_id}/reverse")
    assert response.status_code == 409
    assert response.json()["error"]["reason"] == "already_reversed"


def test_reversal_insufficient_funds(client):
    """Test reversal when payee has insufficient funds."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    client.post("/v1/wallets", json={"id": "charlie"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Set policy to auto-approve
    client.put(
        "/v1/wallets/alice/policy",
        json={"trusted_contacts": ["bob"], "auto_approve_limit_cents": 10000},
    )
    
    # Alice pays bob 5000
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 5000},
        headers={"Idempotency-Key": "tx1"},
    )
    transfer_id = response.json()["id"]
    assert response.json()["status"] == "completed"
    
    # Bob spends it all to charlie
    client.post("/v1/wallets/charlie")
    client.put(
        "/v1/wallets/bob/policy",
        json={"trusted_contacts": ["charlie"], "auto_approve_limit_cents": 10000},
    )
    
    client.post(
        "/v1/transfers",
        json={"from": "bob", "to": "charlie", "amount_cents": 5000},
        headers={"Idempotency-Key": "tx2"},
    )
    
    # Try to reverse - should fail
    response = client.post(f"/v1/transfers/{transfer_id}/reverse")
    assert response.status_code == 409
    assert response.json()["error"]["reason"] == "insufficient_funds"
    
    # Verify no postings were written
    response = client.get("/v1/wallets/alice")
    assert response.json()["balance"] == 5000  # unchanged
