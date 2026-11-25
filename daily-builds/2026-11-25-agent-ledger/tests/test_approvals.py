"""Tests for approval tokens."""

import hmac
from unittest.mock import patch

import pytest


def test_valid_approval_token(client):
    """Test valid approval token completes transfer."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Create pending transfer
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 5000},
        headers={"Idempotency-Key": "tx1"},
    )
    assert response.status_code == 201
    result = response.json()
    assert result["status"] == "pending_approval"
    token = result["approval_token"]
    transfer_id = result["id"]
    
    # Approve
    response = client.post(
        f"/v1/transfers/{transfer_id}/approve",
        json={"token": token},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    
    # Check balance
    response = client.get("/v1/wallets/alice")
    assert response.json()["balance"] == 5000


def test_token_for_different_transfer(client, app):
    """Test token for transfer A used on transfer B."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    client.post("/v1/wallets", json={"id": "charlie"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 20000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Create two pending transfers
    response1 = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 5000},
        headers={"Idempotency-Key": "tx1"},
    )
    token1 = response1.json()["approval_token"]
    
    response2 = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "charlie", "amount_cents": 6000},
        headers={"Idempotency-Key": "tx2"},
    )
    transfer_id_2 = response2.json()["id"]
    
    # Try to use token1 on transfer2
    response = client.post(
        f"/v1/transfers/{transfer_id_2}/approve",
        json={"token": token1},
    )
    assert response.status_code == 403
    assert response.json()["error"]["reason"] == "token_mismatch"


def test_tampered_token(client):
    """Test tampered token is rejected."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 5000},
        headers={"Idempotency-Key": "tx1"},
    )
    token = response.json()["approval_token"]
    transfer_id = response.json()["id"]
    
    # Tamper with token
    tampered_token = token[:-4] + "0000"
    
    response = client.post(
        f"/v1/transfers/{transfer_id}/approve",
        json={"token": tampered_token},
    )
    assert response.status_code == 403


def test_expired_token(client, clock):
    """Test expired token is rejected."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 5000},
        headers={"Idempotency-Key": "tx1"},
    )
    token = response.json()["approval_token"]
    transfer_id = response.json()["id"]
    
    # Advance exactly 15 minutes - should still be valid
    clock.advance(minutes=15)
    
    response = client.post(
        f"/v1/transfers/{transfer_id}/approve",
        json={"token": token},
    )
    assert response.status_code == 200
    
    # Create another transfer
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 3000},
        headers={"Idempotency-Key": "tx2"},
    )
    token2 = response.json()["approval_token"]
    transfer_id_2 = response.json()["id"]
    
    # Advance 15 min + 1 sec - should be expired
    clock.advance(minutes=15, seconds=1)
    
    response = client.post(
        f"/v1/transfers/{transfer_id_2}/approve",
        json={"token": token2},
    )
    assert response.status_code == 403
    assert response.json()["error"]["reason"] == "token_expired"


def test_reused_token(client):
    """Test reused token is rejected."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 5000},
        headers={"Idempotency-Key": "tx1"},
    )
    token = response.json()["approval_token"]
    transfer_id = response.json()["id"]
    
    # First use - ok
    response = client.post(
        f"/v1/transfers/{transfer_id}/approve",
        json={"token": token},
    )
    assert response.status_code == 200
    
    # Second use - rejected
    response = client.post(
        f"/v1/transfers/{transfer_id}/approve",
        json={"token": token},
    )
    assert response.status_code == 403
    assert response.json()["error"]["reason"] == "token_used"


def test_deny_then_approve(client):
    """Test deny, then approve is rejected."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 5000},
        headers={"Idempotency-Key": "tx1"},
    )
    token = response.json()["approval_token"]
    transfer_id = response.json()["id"]
    
    # Deny
    response = client.post(f"/v1/transfers/{transfer_id}/deny")
    assert response.status_code == 200
    assert response.json()["status"] == "denied"
    
    # Try to approve - should fail
    response = client.post(
        f"/v1/transfers/{transfer_id}/approve",
        json={"token": token},
    )
    assert response.status_code == 409


def test_hmac_compare_digest_used(app):
    """Test that hmac.compare_digest is used for constant-time comparison."""
    # This test verifies that the approval manager uses compare_digest
    # by checking it's called during validation
    
    with patch.object(hmac, 'compare_digest', wraps=hmac.compare_digest) as mock_compare:
        approvals = app.state.approvals
        
        # Generate a token
        token = approvals.generate_token(1, "alice", "bob", 1000)
        
        # Validate it
        try:
            approvals.validate_token(1, token)
        except Exception:
            pass
        
        # Verify compare_digest was called
        assert mock_compare.call_count >= 1
