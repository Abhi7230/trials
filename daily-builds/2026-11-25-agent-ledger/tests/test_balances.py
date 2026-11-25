"""Test to verify exact policy walkthrough balances."""

def test_policy_walkthrough_exact_balances(client, clock):
    """Verify exact balances from policy walkthrough match spec."""
    # Setup: Create wallets
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    client.post("/v1/wallets", json={"id": "erin"})
    client.post("/v1/wallets", json={"id": "chen"})
    
    # Alice deposits 50000
    client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 50000},
        headers={"Idempotency-Key": "deposit-1"},
    )
    
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
    
    # Execute transfers as per walkthrough
    # Steps 1-2: Pay bob 2000, 2500 (completed)
    client.post("/v1/transfers", json={"from": "alice", "to": "bob", "amount_cents": 2000}, headers={"Idempotency-Key": "tx-1"})
    client.post("/v1/transfers", json={"from": "alice", "to": "bob", "amount_cents": 2500}, headers={"Idempotency-Key": "tx-2"})
    
    # Step 3: Pay bob 2501 (pending)
    r3 = client.post("/v1/transfers", json={"from": "alice", "to": "bob", "amount_cents": 2501}, headers={"Idempotency-Key": "tx-3"})
    token_3 = r3.json()["approval_token"]
    transfer_3_id = r3.json()["id"]
    
    # Step 4: Pay erin 10000 (pending)
    r4 = client.post("/v1/transfers", json={"from": "alice", "to": "erin", "amount_cents": 10000}, headers={"Idempotency-Key": "tx-4"})
    token_4 = r4.json()["approval_token"]
    transfer_4_id = r4.json()["id"]
    
    # Step 5: Pay erin 10001 (rejected)
    client.post("/v1/transfers", json={"from": "alice", "to": "erin", "amount_cents": 10001}, headers={"Idempotency-Key": "tx-5"})
    
    # Steps 6-7: Approve #3 and #4
    client.post(f"/v1/transfers/{transfer_3_id}/approve", json={"token": token_3})
    client.post(f"/v1/transfers/{transfer_4_id}/approve", json={"token": token_4})
    
    # Step 8: Pay bob 2000
    r8 = client.post("/v1/transfers", json={"from": "alice", "to": "bob", "amount_cents": 2000}, headers={"Idempotency-Key": "tx-8"})
    transfer_8_id = r8.json()["id"]
    
    # Step 9: Pay chen 6000, approve (rejected/daily_cap)
    r9 = client.post("/v1/transfers", json={"from": "alice", "to": "chen", "amount_cents": 6000}, headers={"Idempotency-Key": "tx-9"})
    token_9 = r9.json()["approval_token"]
    transfer_9_id = r9.json()["id"]
    client.post(f"/v1/transfers/{transfer_9_id}/approve", json={"token": token_9})
    
    # Step 10: Pay chen 5999, approve (completed)
    r10 = client.post("/v1/transfers", json={"from": "alice", "to": "chen", "amount_cents": 5999}, headers={"Idempotency-Key": "tx-10"})
    token_10 = r10.json()["approval_token"]
    transfer_10_id = r10.json()["id"]
    client.post(f"/v1/transfers/{transfer_10_id}/approve", json={"token": token_10})
    
    # Step 11: Reverse #8
    client.post(f"/v1/transfers/{transfer_8_id}/reverse")
    
    # Verify exact balances: alice 27000, bob 7001, erin 10000, chen 5999
    # Sum should be 50000 (balancing -50000 from external:funding)
    r_alice = client.get("/v1/wallets/alice")
    r_bob = client.get("/v1/wallets/bob")
    r_erin = client.get("/v1/wallets/erin")
    r_chen = client.get("/v1/wallets/chen")
    
    alice_balance = r_alice.json()["balance"]
    bob_balance = r_bob.json()["balance"]
    erin_balance = r_erin.json()["balance"]
    chen_balance = r_chen.json()["balance"]
    
    print(f"\nFinal balances:")
    print(f"  alice: {alice_balance} (expected 27000)")
    print(f"  bob: {bob_balance} (expected 7001)")
    print(f"  erin: {erin_balance} (expected 10000)")
    print(f"  chen: {chen_balance} (expected 5999)")
    print(f"  sum: {alice_balance + bob_balance + erin_balance + chen_balance} (expected 50000)")
    print(f"  implied external:funding: {-(alice_balance + bob_balance + erin_balance + chen_balance)} (expected -50000)")
    
    assert alice_balance == 27000, f"Alice should have 27000, got {alice_balance}"
    assert bob_balance == 7001, f"Bob should have 7001, got {bob_balance}"
    assert erin_balance == 10000, f"Erin should have 10000, got {erin_balance}"
    assert chen_balance == 5999, f"Chen should have 5999, got {chen_balance}"
    
    # Verify sum equals 50000 (balancing -50000 from external:funding)
    total = alice_balance + bob_balance + erin_balance + chen_balance
    assert total == 50000, f"Sum should be 50000, got {total}"
