"""Tests for rate and budget limits."""

import pytest

from modelgate.limits import LimitExceededError, LimitsManager


class FakeClock:
    """Fake clock for testing."""

    def __init__(self):
        self.time = 0.0

    def __call__(self):
        return self.time

    def advance(self, seconds: float):
        self.time += seconds


def test_token_bucket_refills():
    """Test token bucket refills over time."""
    clock = FakeClock()
    limits = LimitsManager(
        default_daily_usd=100.0,
        default_rpm=60,
        default_tpm=1000,
        clock=clock,
    )

    # Consume all RPM tokens
    for _ in range(60):
        limits.check_and_consume("key1", tokens=10, cost_usd=0.01)

    # Should be exhausted
    with pytest.raises(LimitExceededError, match="requests per minute"):
        limits.check_and_consume("key1", tokens=10, cost_usd=0.01)

    # Advance time - tokens should refill
    clock.advance(60)  # 1 minute = full refill

    # Should work now
    limits.check_and_consume("key1", tokens=10, cost_usd=0.01)


def test_daily_budget_limit():
    """Test daily budget cap."""
    clock = FakeClock()
    limits = LimitsManager(
        default_daily_usd=10.0,
        default_rpm=1000,
        default_tpm=100000,
        clock=clock,
    )

    # Consume $9 - should work
    limits.check_and_consume("key1", tokens=100, cost_usd=9.0)

    # Try to consume $2 more - should fail
    with pytest.raises(LimitExceededError, match="Daily budget"):
        limits.check_and_consume("key1", tokens=100, cost_usd=2.0)


def test_daily_reset():
    """Test daily budget resets after 24 hours."""
    clock = FakeClock()
    limits = LimitsManager(
        default_daily_usd=10.0,
        default_rpm=1000,
        default_tpm=100000,
        clock=clock,
    )

    # Consume budget
    limits.check_and_consume("key1", tokens=100, cost_usd=9.0)

    # Advance 24 hours
    clock.advance(86400)

    # Should be reset - can consume again
    limits.check_and_consume("key1", tokens=100, cost_usd=9.0)


def test_keys_isolated():
    """Test API keys have isolated limits."""
    limits = LimitsManager(
        default_daily_usd=10.0,
        default_rpm=60,
        default_tpm=1000,
    )

    # key1 consumes budget
    limits.check_and_consume("key1", tokens=100, cost_usd=9.0)

    # key2 should have full budget
    limits.check_and_consume("key2", tokens=100, cost_usd=9.0)


def test_tpm_limit():
    """Test tokens per minute limit."""
    clock = FakeClock()
    limits = LimitsManager(
        default_daily_usd=100.0,
        default_rpm=1000,
        default_tpm=1000,
        clock=clock,
    )

    # Consume all tokens
    limits.check_and_consume("key1", tokens=1000, cost_usd=0.01)

    # Should be exhausted
    with pytest.raises(LimitExceededError, match="tokens per minute"):
        limits.check_and_consume("key1", tokens=10, cost_usd=0.01)

    # Refill over time
    clock.advance(60)

    # Should work now
    limits.check_and_consume("key1", tokens=100, cost_usd=0.01)


def test_remaining_budget():
    """Test remaining budget calculation."""
    limits = LimitsManager(
        default_daily_usd=100.0,
        default_rpm=1000,
        default_tpm=100000,
    )

    remaining = limits.get_remaining_budget("key1")
    assert remaining == 100.0

    limits.check_and_consume("key1", tokens=100, cost_usd=25.0)

    remaining = limits.get_remaining_budget("key1")
    assert remaining == 75.0
