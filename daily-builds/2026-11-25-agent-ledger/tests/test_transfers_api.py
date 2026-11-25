"""Tests for transfers API."""

import pytest


def test_create_transfer_basic(client):
    """Test basic transfer creation."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    client.put(
        "/v1/wallets/alice/policy",
        json={"trusted_contacts": ["bob"], "auto_approve_limit_cents": 5000},
    )
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 1000, "memo": "Test"},
        headers={"Idempotency-Key": "tx1"},
    )
    
    assert response.status_code == 201
    result = response.json()
    assert result["status"] == "completed"
    assert result["from_wallet"] == "alice"
    assert result["to"] == "bob"
    assert result["amount_cents"] == 1000


def test_get_transfer(client):
    """Test getting transfer details."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    client.put(
        "/v1/wallets/alice/policy",
        json={"trusted_contacts": ["bob"], "auto_approve_limit_cents": 5000},
    )
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 1000},
        headers={"Idempotency-Key": "tx1"},
    )
    transfer_id = response.json()["id"]
    
    response = client.get(f"/v1/transfers/{transfer_id}")
    assert response.status_code == 200
    assert response.json()["id"] == transfer_id


def test_insufficient_funds(client):
    """Test transfer with insufficient funds."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 500},
        headers={"Idempotency-Key": "d1"},
    )
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 1000},
        headers={"Idempotency-Key": "tx1"},
    )
    
    assert response.status_code == 409
    assert response.json()["error"]["reason"] == "insufficient_funds"
