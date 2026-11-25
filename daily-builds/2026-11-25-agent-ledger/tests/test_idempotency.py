"""Tests for idempotency."""

import pytest


def test_idempotency_replay(client):
    """Test idempotent replay of same request."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # First request
    response1 = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 1000},
        headers={"Idempotency-Key": "tx1"},
    )
    assert response1.status_code == 201
    transfer_id_1 = response1.json()["id"]
    
    # Same request again - should replay
    response2 = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 1000},
        headers={"Idempotency-Key": "tx1"},
    )
    assert response2.status_code == 201
    assert response2.headers.get("Idempotent-Replayed") == "true"
    assert response2.json()["id"] == transfer_id_1
    
    # Verify only one journal entry was created
    response = client.get("/v1/wallets/alice")
    assert response.json()["balance"] == 9000


def test_idempotency_replay_multiple_times(client):
    """Test replaying same request 5 times."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Make same request 5 times
    responses = []
    for i in range(5):
        response = client.post(
            "/v1/transfers",
            json={"from": "alice", "to": "bob", "amount_cents": 1000},
            headers={"Idempotency-Key": "tx1"},
        )
        responses.append(response)
    
    # First request created it
    assert responses[0].status_code == 201
    transfer_id = responses[0].json()["id"]
    
    # Remaining 4 are replays
    for response in responses[1:]:
        assert response.status_code == 201
        assert response.headers.get("Idempotent-Replayed") == "true"
        assert response.json()["id"] == transfer_id
    
    # Only one journal entry
    response = client.get("/v1/wallets/alice")
    assert response.json()["balance"] == 9000


def test_idempotency_key_reused_different_body(client):
    """Test rejection when key is reused with different body."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # First request
    response1 = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 1000},
        headers={"Idempotency-Key": "tx1"},
    )
    assert response1.status_code == 201
    
    # Same key, different amount
    response2 = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 2000},
        headers={"Idempotency-Key": "tx1"},
    )
    assert response2.status_code == 409
    assert response2.json()["error"]["reason"] == "idempotency_key_reused"


def test_idempotency_missing_key(client):
    """Test rejection when idempotency key is missing."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 1000},
    )
    assert response.status_code == 400


def test_idempotency_policy_rejection_replay(client):
    """Test that policy rejections are replayed."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 1000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Request that will be rejected
    response1 = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 10000},
        headers={"Idempotency-Key": "tx1"},
    )
    assert response1.status_code == 409
    assert response1.json()["error"]["reason"] == "insufficient_funds"
    
    # Same request - should replay rejection
    response2 = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 10000},
        headers={"Idempotency-Key": "tx1"},
    )
    assert response2.status_code == 409
    assert response2.headers.get("Idempotent-Replayed") == "true"
    assert response2.json()["error"]["reason"] == "insufficient_funds"


def test_idempotency_scoped_per_wallet(client):
    """Test that keys are scoped per wallet."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "charlie"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    client.post(
        "/v1/wallets/charlie/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d2"},
    )
    
    # Same key on two different wallets
    response1 = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 1000},
        headers={"Idempotency-Key": "same-key"},
    )
    assert response1.status_code == 201
    id1 = response1.json()["id"]
    
    response2 = client.post(
        "/v1/transfers",
        json={"from": "charlie", "to": "bob", "amount_cents": 1000},
        headers={"Idempotency-Key": "same-key"},
    )
    assert response2.status_code == 201
    id2 = response2.json()["id"]
    
    # Should create two different transfers
    assert id1 != id2


def test_idempotency_422_not_stored(client):
    """Test that 422 validation errors are not stored."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    # Invalid request (negative amount)
    response1 = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": -100},
        headers={"Idempotency-Key": "tx1"},
    )
    assert response1.status_code == 422
    
    # Corrected request with same key should succeed
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    response2 = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 100},
        headers={"Idempotency-Key": "tx1"},
    )
    assert response2.status_code == 201


def test_idempotency_purge_old_keys(client, clock, app):
    """Test purging old idempotency keys."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Create transfer
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 1000},
        headers={"Idempotency-Key": "tx1"},
    )
    assert response.status_code == 201
    
    # Advance 25 hours
    clock.advance(hours=25)
    
    # Purge old keys
    idempotency = app.state.idempotency
    count = idempotency.purge_old_keys()
    assert count >= 1
    
    # Same key should create new transfer
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 1000},
        headers={"Idempotency-Key": "tx1"},
    )
    assert response.status_code == 201
    # Should not have replay header
    assert "Idempotent-Replayed" not in response.headers
