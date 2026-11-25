"""Tests for concurrency."""

import threading

import pytest


def test_overdraft_race(client, app):
    """Test that concurrent transfers cannot overdraft wallet."""
    # Setup
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 1000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Set policy for auto-approval
    client.put(
        "/v1/wallets/alice/policy",
        json={
            "per_tx_cap_cents": 10**9,
            "daily_cap_cents": 10**9,
            "auto_approve_limit_cents": 100,
            "trusted_contacts": ["bob"],
        },
    )
    
    # 50 threads each trying to pay 100
    num_threads = 50
    results = []
    
    def make_transfer(i):
        try:
            response = client.post(
                "/v1/transfers",
                json={"from": "alice", "to": "bob", "amount_cents": 100},
                headers={"Idempotency-Key": f"tx-{i}"},
            )
            results.append({
                "status_code": response.status_code,
                "response": response.json(),
            })
        except Exception as e:
            results.append({"error": str(e)})
    
    threads = [threading.Thread(target=make_transfer, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Count successes and failures
    completed = sum(1 for r in results if r.get("status_code") == 201 and r["response"].get("status") == "completed")
    rejected = sum(1 for r in results if r.get("status_code") == 409)
    
    # Exactly 10 should complete
    assert completed == 10
    assert rejected == 40
    
    # Final balance should be 0
    response = client.get("/v1/wallets/alice")
    assert response.json()["balance"] == 0
    
    response = client.get("/v1/wallets/bob")
    assert response.json()["balance"] == 1000


def test_daily_cap_race(client):
    """Test concurrent transfers against daily cap."""
    # Setup
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 100000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Set policy
    client.put(
        "/v1/wallets/alice/policy",
        json={
            "per_tx_cap_cents": 10**9,
            "daily_cap_cents": 9500,
            "auto_approve_limit_cents": 1000,
            "trusted_contacts": ["bob"],
        },
    )
    
    # 10 threads each trying to pay 1000
    num_threads = 10
    results = []
    
    def make_transfer(i):
        try:
            response = client.post(
                "/v1/transfers",
                json={"from": "alice", "to": "bob", "amount_cents": 1000},
                headers={"Idempotency-Key": f"tx-{i}"},
            )
            results.append({
                "status_code": response.status_code,
                "response": response.json(),
            })
        except Exception as e:
            results.append({"error": str(e)})
    
    threads = [threading.Thread(target=make_transfer, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Count completed
    completed = sum(1 for r in results if r.get("status_code") == 201 and r["response"].get("status") == "completed")
    
    # Exactly 9 should complete (9 * 1000 = 9000, which is < 9500)
    assert completed == 9


def test_same_key_race(client):
    """Test concurrent requests with same idempotency key."""
    # Setup
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 100000},
        headers={"Idempotency-Key": "d1"},
    )
    
    # Set auto-approval policy
    client.put(
        "/v1/wallets/alice/policy",
        json={"trusted_contacts": ["bob"], "auto_approve_limit_cents": 10000},
    )
    
    # 20 threads with same key and body
    num_threads = 20
    results = []
    
    def make_transfer():
        try:
            response = client.post(
                "/v1/transfers",
                json={"from": "alice", "to": "bob", "amount_cents": 1000},
                headers={"Idempotency-Key": "same-key"},
            )
            results.append({
                "status_code": response.status_code,
                "response": response.json(),
            })
        except Exception as e:
            results.append({"error": str(e)})
    
    threads = [threading.Thread(target=make_transfer) for _ in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Should have at least one success
    successes = [r for r in results if r.get("status_code") == 201]
    assert len(successes) >= 1
    
    # All successful responses should have same transfer ID
    if len(successes) > 0:
        transfer_ids = [r["response"]["id"] for r in successes]
        assert len(set(transfer_ids)) == 1
    
    # Only one journal entry should be created
    response = client.get("/v1/wallets/alice")
    assert response.json()["balance"] == 99000


def test_concurrency_repeated():
    """Run concurrency tests multiple times to catch flakiness."""
    # This is a wrapper that runs each test 3 times
    # In real execution, pytest would be run with this test
    pass  # The actual tests above will be run 3 times manually or via pytest-repeat


@pytest.mark.parametrize("run", [1, 2, 3])
def test_overdraft_race_repeated(client, app, run):
    """Run overdraft race test 3 times."""
    test_overdraft_race(client, app)


@pytest.mark.parametrize("run", [1, 2, 3])
def test_daily_cap_race_repeated(client, run):
    """Run daily cap race test 3 times."""
    test_daily_cap_race(client)


@pytest.mark.parametrize("run", [1, 2, 3])
def test_same_key_race_repeated(client, run):
    """Run same key race test 3 times."""
    test_same_key_race(client)
