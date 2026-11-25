"""Tests for money requests API."""

import pytest


def test_create_money_request(client):
    """Test creating a money request."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    response = client.post(
        "/v1/requests",
        json={
            "from": "alice",
            "to": "bob",
            "amount_cents": 1000,
            "memo": "Lunch money",
        },
    )
    
    assert response.status_code == 201
    result = response.json()
    assert result["from_wallet"] == "alice"
    assert result["to"] == "bob"
    assert result["amount_cents"] == 1000
    assert result["status"] == "pending"


def test_pay_money_request(client):
    """Test paying a money request."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    # Bob deposits money
    client.post(
        "/v1/wallets/bob/deposits",
        json={"amount_cents": 5000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Alice requests money from bob
    response = client.post(
        "/v1/requests",
        json={"from": "alice", "to": "bob", "amount_cents": 1000},
    )
    request_id = response.json()["id"]
    
    # Set bob's policy to auto-approve
    client.put(
        "/v1/wallets/bob/policy",
        json={"trusted_contacts": ["alice"], "auto_approve_limit_cents": 2000},
    )
    
    # Bob pays the request
    response = client.post(
        f"/v1/requests/{request_id}/pay",
        headers={"Idempotency-Key": "pay-1"},
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "paid"
    
    # Check balances
    response = client.get("/v1/wallets/alice")
    assert response.json()["balance"] == 1000
    
    response = client.get("/v1/wallets/bob")
    assert response.json()["balance"] == 4000


def test_decline_money_request(client):
    """Test declining a money request."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    response = client.post(
        "/v1/requests",
        json={"from": "alice", "to": "bob", "amount_cents": 1000},
    )
    request_id = response.json()["id"]
    
    response = client.post(f"/v1/requests/{request_id}/decline")
    assert response.status_code == 200
    assert response.json()["status"] == "declined"


def test_cancel_money_request(client):
    """Test cancelling a money request."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    response = client.post(
        "/v1/requests",
        json={"from": "alice", "to": "bob", "amount_cents": 1000},
    )
    request_id = response.json()["id"]
    
    response = client.post(f"/v1/requests/{request_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
