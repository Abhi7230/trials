"""Tests for bill splitting."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from agent_ledger.split import BillSplitter, allocate_by_largest_remainder


def test_allocate_exact_examples():
    """Test exact allocation examples from spec."""
    assert allocate_by_largest_remainder(10000, [1, 1, 1]) == [3334, 3333, 3333]
    assert allocate_by_largest_remainder(1, [1, 1, 1]) == [1, 0, 0]
    assert allocate_by_largest_remainder(100, [1, 2, 3]) == [17, 33, 50]
    assert allocate_by_largest_remainder(1000, [1, 1, 1, 1, 1, 1, 1]) == [
        143,
        143,
        143,
        143,
        143,
        143,
        142,
    ]


def test_equal_split_exact():
    """Test equal split with exact numbers."""
    # Subtotal 15000, tax 8.875% → 1331, tip 20% → 3000, total 19331 / 3
    tax = int(round(15000 * 0.08875))
    assert tax == 1331
    
    tip = int(round(15000 * 0.20))
    assert tip == 3000
    
    total = 15000 + 1331 + 3000
    assert total == 19331
    
    split = allocate_by_largest_remainder(total, [1, 1, 1])
    assert split == [6444, 6444, 6443]
    assert sum(split) == total


def test_dinner_fixture(client):
    """Test dinner split from spec."""
    # Create wallets
    client.post("/v1/wallets", json={"id": "alice"})
    client.post("/v1/wallets", json={"id": "bob"})
    client.post("/v1/wallets", json={"id": "chen"})
    client.post("/v1/wallets", json={"id": "dev"})
    
    # Split bill
    response = client.post(
        "/v1/splits",
        json={
            "payer": "alice",
            "participants": ["alice", "bob", "chen", "dev"],
            "items": [
                {"owner": "alice", "amount_cents": 4200},
                {"owner": "bob", "amount_cents": 3850},
                {"owner": "chen", "amount_cents": 5100},
                {"owner": "dev", "amount_cents": 2975},
                {"amount_cents": 1800},  # shared
            ],
            "tax_rate": 0.08875,
            "tip_rate": 0.18,
            "tip_base": "pre_tax",
        },
    )
    
    assert response.status_code == 201
    result = response.json()
    
    # Check subtotal
    assert result["items_total_cents"] == 17925
    
    # Check tax
    assert result["tax_cents"] == 1591
    
    # Check tip (ROUND_HALF_UP, not banker's rounding)
    assert result["tip_cents"] == 3227  # Not 3226
    
    # Check grand total
    assert result["grand_total_cents"] == 22743
    
    # Check shares
    shares = {s["participant"]: s for s in result["shares"]}
    
    assert shares["alice"]["total_cents"] == 5900
    assert shares["bob"]["total_cents"] == 5456
    assert shares["chen"]["total_cents"] == 7041
    assert shares["dev"]["total_cents"] == 4346
    
    # Check requests created (3, not for alice)
    assert len(result["requests_created"]) == 3


def test_too_many_participants(client):
    """Test rejection of too many participants."""
    client.post("/v1/wallets", json={"id": "payer"})
    
    participants = [f"p{i}" for i in range(101)]
    for p in participants:
        client.post("/v1/wallets", json={"id": p})
    
    response = client.post(
        "/v1/splits",
        json={
            "payer": "payer",
            "participants": participants,
            "items": [{"amount_cents": 1000}],
        },
    )
    
    assert response.status_code == 422


@given(
    total=st.integers(min_value=0, max_value=10**9),
    num_weights=st.integers(min_value=1, max_value=100),
)
@settings(max_examples=300, derandomize=True)
def test_allocation_property(total, num_weights):
    """Property test: allocation sums to total and shares are proportional."""
    weights = [1] * num_weights
    allocation = allocate_by_largest_remainder(total, weights)
    
    # Sum equals total
    assert sum(allocation) == total
    
    # Each share differs from exact by < 1
    exact = total / num_weights
    for share in allocation:
        assert abs(share - exact) < 1
