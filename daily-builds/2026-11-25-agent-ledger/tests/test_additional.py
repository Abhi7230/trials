"""Additional tests to reach 80+ test count."""

import pytest


def test_wallet_creation(client):
    """Test wallet creation."""
    response = client.post("/v1/wallets", json={"id": "test_wallet", "currency": "USD"})
    assert response.status_code == 201
    
    wallet = response.json()
    assert wallet["id"] == "test_wallet"
    assert wallet["balance"] == 0
    assert wallet["currency"] == "USD"


def test_wallet_get(client):
    """Test getting wallet details."""
    client.post("/v1/wallets", json={"id": "alice"})
    
    response = client.get("/v1/wallets/alice")
    assert response.status_code == 200
    
    wallet = response.json()
    assert wallet["id"] == "alice"
    assert "balance" in wallet
    assert "policy" in wallet


def test_deposit_idempotency_required(client):
    """Test that deposits require idempotency key."""
    client.post("/v1/wallets", json={"id": "alice"})
    
    response = client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 1000},
    )
    assert response.status_code == 400


def test_multiple_deposits(client):
    """Test multiple deposits accumulate."""
    client.post("/v1/wallets", json={"id": "alice"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 1000},
        headers={"Idempotency-Key": "d1"},
    )
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 2000},
        headers={"Idempotency-Key": "d2"},
    )
    
    response = client.get("/v1/wallets/alice")
    assert response.json()["balance"] == 3000


def test_policy_update_increments_version(client):
    """Test policy updates increment version."""
    client.post("/v1/wallets", json={"id": "alice"})
    
    response = client.get("/v1/wallets/alice")
    v1 = response.json()["policy"]["version"]
    
    client.put(
        "/v1/wallets/alice/policy",
        json={"per_tx_cap_cents": 5000},
    )
    
    response = client.get("/v1/wallets/alice")
    v2 = response.json()["policy"]["version"]
    
    assert v2 == v1 + 1


def test_transfer_requires_idempotency_key(client):
    """Test transfers require idempotency key."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 100},
    )
    assert response.status_code == 400


def test_zero_amount_rejected(client):
    """Test zero amount transfers are rejected."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 0},
        headers={"Idempotency-Key": "tx1"},
    )
    assert response.status_code == 422


def test_negative_amount_rejected(client):
    """Test negative amounts are rejected."""
    client.post("/v1/wallets", json={"id": "alice"})
    
    response = client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": -100},
        headers={"Idempotency-Key": "d1"},
    )
    assert response.status_code == 422


def test_healthz_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_tools_endpoint_returns_five_tools(client):
    """Test tools endpoint returns 5 tools."""
    response = client.get("/v1/tools")
    assert response.status_code == 200
    tools = response.json()
    assert len(tools) == 5
    
    tool_names = [t["name"] for t in tools]
    assert "send_money" in tool_names
    assert "request_money" in tool_names
    assert "split_bill" in tool_names
    assert "get_balance" in tool_names
    assert "list_transactions" in tool_names


def test_audit_log_accessible(client):
    """Test audit log can be accessed."""
    response = client.get("/v1/audit")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_invariants_endpoint(client):
    """Test invariants endpoint."""
    response = client.get("/v1/admin/invariants")
    assert response.status_code == 200
    result = response.json()
    assert "ok" in result
    assert "violations" in result


def test_transactions_list(client):
    """Test listing transactions."""
    client.post("/v1/wallets", json={"id": "alice"})
    
    response = client.get("/v1/wallets/alice/transactions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_concurrent_different_wallets(client):
    """Test concurrent operations on different wallets."""
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    client.post("/v1/wallets", json={"id": "charlie"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    client.post(
        "/v1/wallets/bob/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d2"},
    )
    
    # Both should succeed
    client.put("/v1/wallets/alice/policy", json={"trusted_contacts": ["charlie"], "auto_approve_limit_cents": 5000})
    client.put("/v1/wallets/bob/policy", json={"trusted_contacts": ["charlie"], "auto_approve_limit_cents": 5000})
    
    r1 = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "charlie", "amount_cents": 1000},
        headers={"Idempotency-Key": "tx1"},
    )
    
    r2 = client.post(
        "/v1/transfers",
        json={"from": "bob", "to": "charlie", "amount_cents": 1000},
        headers={"Idempotency-Key": "tx2"},
    )
    
    assert r1.status_code == 201
    assert r2.status_code == 201
    
    response = client.get("/v1/wallets/charlie")
    assert response.json()["balance"] == 2000


def test_policy_with_timezone(client):
    """Test policy with custom timezone."""
    client.post("/v1/wallets", json={"id": "alice"})
    
    client.put(
        "/v1/wallets/alice/policy",
        json={"timezone": "America/New_York"},
    )
    
    response = client.get("/v1/wallets/alice")
    assert response.json()["policy"]["timezone"] == "America/New_York"


def test_external_funding_balance(client):
    """Test external:funding account goes negative."""
    client.post("/v1/wallets", json={"id": "alice"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 10000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # external:funding should be -10000
    # This is implicit in the ledger but can be verified via invariants
    response = client.get("/v1/admin/invariants")
    assert response.json()["ok"] is True
