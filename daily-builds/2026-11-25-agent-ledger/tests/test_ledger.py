"""Tests for ledger operations."""

import pytest

from agent_ledger.errors import InsufficientFundsError


def test_create_journal_entry_balanced(app, clock):
    """Test creating balanced journal entry."""
    ledger = app.state.ledger
    
    # Create wallets
    ledger.create_wallet("alice", "USD", clock.now())
    ledger.create_wallet("bob", "USD", clock.now())
    
    # Create balanced entry
    entry_id = ledger.create_journal_entry(
        "transfer",
        [("alice", -100), ("bob", 100)],
        clock.now(),
    )
    
    assert entry_id > 0


def test_create_journal_entry_unbalanced_rejected(app, clock):
    """Test unbalanced entry is rejected."""
    ledger = app.state.ledger
    
    ledger.create_wallet("alice", "USD", clock.now())
    ledger.create_wallet("bob", "USD", clock.now())
    
    with pytest.raises(ValueError, match="sum to zero"):
        ledger.create_journal_entry(
            "transfer",
            [("alice", -100), ("bob", 50)],
            clock.now(),
        )


def test_wallet_balance_cannot_go_negative(app, clock):
    """Test wallet balance cannot go negative."""
    ledger = app.state.ledger
    
    ledger.create_wallet("alice", "USD", clock.now())
    ledger.create_wallet("bob", "USD", clock.now())
    
    with pytest.raises(InsufficientFundsError):
        ledger.create_journal_entry(
            "transfer",
            [("alice", -100), ("bob", 100)],
            clock.now(),
        )


def test_system_accounts_can_go_negative(app, clock):
    """Test system accounts can have negative balance."""
    ledger = app.state.ledger
    
    ledger.create_wallet("alice", "USD", clock.now())
    
    # Deposit from external:funding (goes negative)
    entry_id = ledger.create_journal_entry(
        "deposit",
        [("external:funding", -1000), ("alice", 1000)],
        clock.now(),
    )
    
    assert entry_id > 0
    assert ledger.get_balance("external:funding") == -1000
    assert ledger.get_balance("alice") == 1000


def test_get_balance(app, clock):
    """Test getting account balance."""
    ledger = app.state.ledger
    
    ledger.create_wallet("alice", "USD", clock.now())
    
    # Initial balance is 0
    assert ledger.get_balance("alice") == 0
    
    # After deposit
    ledger.create_journal_entry(
        "deposit",
        [("external:funding", -1000), ("alice", 1000)],
        clock.now(),
    )
    
    assert ledger.get_balance("alice") == 1000


def test_cached_balance_updated(app, clock):
    """Test cached balance is updated correctly."""
    ledger = app.state.ledger
    
    ledger.create_wallet("alice", "USD", clock.now())
    
    # Deposit
    ledger.create_journal_entry(
        "deposit",
        [("external:funding", -1000), ("alice", 1000)],
        clock.now(),
    )
    
    # Check cached balance matches postings sum
    cached = ledger.get_balance("alice")
    postings_sum = ledger.get_postings_sum("alice")
    assert cached == postings_sum == 1000
