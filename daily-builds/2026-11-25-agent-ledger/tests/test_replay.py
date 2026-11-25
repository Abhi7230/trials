"""Tests for scenario replay."""

import json
import tempfile
import pytest
import yaml


def test_replay_dinner_scenario_loads(client):
    """Test that dinner scenario file loads properly."""
    with open("examples/dinner.yaml") as f:
        scenario = yaml.safe_load(f)
    
    assert "steps" in scenario
    assert len(scenario["steps"]) > 0
    
    # Check that split endpoint is included
    split_step = [s for s in scenario["steps"] if s.get("path") == "/v1/splits"]
    assert len(split_step) > 0


def test_replay_policy_walkthrough_loads(client):
    """Test that policy walkthrough scenario file loads properly."""
    with open("examples/policy_walkthrough.yaml") as f:
        scenario = yaml.safe_load(f)
    
    assert "steps" in scenario
    assert len(scenario["steps"]) > 0


def test_replay_simple_scenario(client):
    """Test replaying a simple scenario through the API."""
    # Create wallets
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    
    # Deposit
    response = client.post(
        "/v1/wallets/alice/deposits",
        json={"amount_cents": 1000},
        headers={"Idempotency-Key": "d1"},
    )
    assert response.status_code == 201
    
    # Set policy
    client.put(
        "/v1/wallets/alice/policy",
        json={"trusted_contacts": ["bob"], "auto_approve_limit_cents": 500},
    )
    
    # Transfer
    response = client.post(
        "/v1/transfers",
        json={"from": "alice", "to": "bob", "amount_cents": 300},
        headers={"Idempotency-Key": "tx1"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "completed"
    
    # Check balances
    response = client.get("/v1/wallets/alice")
    assert response.json()["balance"] == 700
    
    response = client.get("/v1/wallets/bob")
    assert response.json()["balance"] == 300
