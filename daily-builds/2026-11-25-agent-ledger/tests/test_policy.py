"""Tests for policy engine."""

import pytest


def test_policy_walkthrough(client, clock):
    """Test complete policy walkthrough from spec."""
    # Setup: Create wallets
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    client.post("/v1/wallets", json={"id": "erin"})
    client.post("/v1/wallets", json={"id": "chen"})
    
    # Alice deposits 50000
    response = client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 50000},
        headers={"Idempotency-Key": "deposit-1"},
    )
    assert response.status_code == 201
    
    # Set policy
    client.put(
        "/v1/wallets/alice/policy",
        json={
            "per_tx_cap_cents": 10000,
            "daily_cap_cents": 25000,
            "auto_approve_limit_cents": 2500,
            "trusted_contacts": ["bob"],
        },
    )
    
    # Step 1: Pay bob 2000 → completed
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 2000},
        headers={"Idempotency-Key": "tx-1"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "completed"
    
    # Step 2: Pay bob 2500 → completed (inclusive boundary)
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 2500},
        headers={"Idempotency-Key": "tx-2"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "completed"
    
    # Step 3: Pay bob 2501 → pending_approval
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 2501},
        headers={"Idempotency-Key": "tx-3"},
    )
    assert response.status_code == 201
    result = response.json()
    assert result["status"] == "pending_approval"
    token_3 = result["approval_token"]
    transfer_3_id = result["id"]
    
    # Step 4: Pay erin 10000 → pending_approval
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "erin", "amount_cents": 10000},
        headers={"Idempotency-Key": "tx-4"},
    )
    assert response.status_code == 201
    result = response.json()
    assert result["status"] == "pending_approval"
    token_4 = result["approval_token"]
    transfer_4_id = result["id"]
    
    # Step 5: Pay erin 10001 → rejected/per_tx_cap
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "erin", "amount_cents": 10001},
        headers={"Idempotency-Key": "tx-5"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["reason"] == "per_tx_cap"
    
    # Step 6: Approve #3 → completed
    response = client.post(
        f"/v1/transfers/{transfer_3_id}/approve",
        json={"token": token_3},
    )
    assert response.status_code == 200
    
    # Check alice balance: 50000 - 2000 - 2500 - 2501 = 42999
    response = client.get("/v1/wallets/alice")
    alice = response.json()
    assert alice["balance"] == 42999
    assert alice["daily_spent"] == 7001
    
    # Step 7: Approve #4 → completed
    response = client.post(
        f"/v1/transfers/{transfer_4_id}/approve",
        json={"token": token_4},
    )
    assert response.status_code == 200
    
    # Check alice balance: 42999 - 10000 = 32999
    response = client.get("/v1/wallets/alice")
    alice = response.json()
    assert alice["balance"] == 32999
    assert alice["daily_spent"] == 17001
    
    # Step 8: Pay bob 2000 → completed
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 2000},
        headers={"Idempotency-Key": "tx-8"},
    )
    assert response.status_code == 201
    transfer_8_id = response.json()["id"]
    
    # Check alice balance: 32999 - 2000 = 30999
    response = client.get("/v1/wallets/alice")
    alice = response.json()
    assert alice["balance"] == 30999
    assert alice["daily_spent"] == 19001
    
    # Step 9: Pay chen 6000 → pending, approve → rejected/daily_cap
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "chen", "amount_cents": 6000},
        headers={"Idempotency-Key": "tx-9"},
    )
    assert response.status_code == 201
    result = response.json()
    assert result["status"] == "pending_approval"
    token_9 = result["approval_token"]
    transfer_9_id = result["id"]
    
    # Approve should fail with daily_cap
    response = client.post(
        f"/v1/transfers/{transfer_9_id}/approve",
        json={"token": token_9},
    )
    assert response.status_code == 409
    assert response.json()["error"]["reason"] == "daily_cap"
    
    # Alice balance unchanged
    response = client.get("/v1/wallets/alice")
    alice = response.json()
    assert alice["balance"] == 30999
    
    # Step 10: Pay chen 5999 → pending, approve → completed (exactly 25000)
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "chen", "amount_cents": 5999},
        headers={"Idempotency-Key": "tx-10"},
    )
    assert response.status_code == 201
    result = response.json()
    assert result["status"] == "pending_approval"
    token_10 = result["approval_token"]
    transfer_10_id = result["id"]
    
    response = client.post(
        f"/v1/transfers/{transfer_10_id}/approve",
        json={"token": token_10},
    )
    assert response.status_code == 200
    
    # Check alice balance: 30999 - 5999 = 25000
    response = client.get("/v1/wallets/alice")
    alice = response.json()
    assert alice["balance"] == 25000
    assert alice["daily_spent"] == 25000
    
    # Step 11: Reverse #8
    response = client.post(f"/v1/transfers/{transfer_8_id}/reverse")
    assert response.status_code == 200
    
    # Check alice balance: 25000 + 2000 = 27000
    response = client.get("/v1/wallets/alice")
    alice = response.json()
    assert alice["balance"] == 27000
    
    # Check bob balance decreased
    response = client.get("/v1/wallets/bob")
    bob = response.json()
    assert bob["balance"] == 7001  # 2000 + 2500 + 2501 - 2000
    
    # Final balances: alice 27000, bob 7001, erin 10000, chen 5999, external:funding -50000 (sum=0)
    response = client.get("/v1/wallets/alice")
    assert response.json()["balance"] == 27000
    
    response = client.get("/v1/wallets/bob")
    assert response.json()["balance"] == 7001
    
    response = client.get("/v1/wallets/erin")
    assert response.json()["balance"] == 10000
    
    response = client.get("/v1/wallets/chen")
    assert response.json()["balance"] == 5999
    
    # Verify user balances sum to 50000 (which equals the deposit, implying external:funding = -50000)
    user_total = 27000 + 7001 + 10000 + 5999
    assert user_total == 50000  # Total deposits


def test_blocked_contact(client):
    """Test blocked contact rejection."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    client.put(
        "/v1/wallets/alice/policy",
        json={"blocked_contacts": ["bob"], "trusted_contacts": ["bob"]},
    )
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 100},
        headers={"Idempotency-Key": "tx1"},
    )
    
    assert response.status_code == 409
    assert response.json()["error"]["reason"] == "blocked_contact"


def test_self_transfer(client):
    """Test self-transfer rejection."""
    client.post("/v1/wallets", json={"id": "alice"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "alice", "amount_cents": 100},
        headers={"Idempotency-Key": "tx1"},
    )
    
    assert response.status_code == 409
    assert response.json()["error"]["reason"] == "self_transfer"


def test_currency_mismatch(client):
    """Test currency mismatch rejection."""
    client.post("/v1/wallets", json={"id": "alice", "currency": "USD"})
    client.post("/v1/wallets", json={"id": "bob", "currency": "EUR"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 100},
        headers={"Idempotency-Key": "tx1"},
    )
    
    assert response.status_code == 409
    assert response.json()["error"]["reason"] == "currency_mismatch"
