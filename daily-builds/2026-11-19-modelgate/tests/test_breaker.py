"""Tests for circuit breaker."""

from modelgate.breaker import BreakerState, CircuitBreaker


class FakeClock:
    """Fake clock for testing."""

    def __init__(self):
        self.time = 0.0

    def __call__(self):
        return self.time

    def advance(self, seconds: float):
        self.time += seconds


def test_breaker_starts_closed():
    """Test breaker starts in closed state."""
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)
    assert breaker.is_available("model-a")
    status = breaker.get_status("model-a")
    assert status.state == BreakerState.CLOSED


def test_breaker_opens_after_threshold_failures():
    """Test breaker opens after N consecutive failures."""
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=60, clock=clock)

    # Record 2 failures - should stay closed
    breaker.record_failure("model-a")
    breaker.record_failure("model-a")
    assert breaker.is_available("model-a")

    # 3rd failure - should open
    breaker.record_failure("model-a")
    assert not breaker.is_available("model-a")
    status = breaker.get_status("model-a")
    assert status.state == BreakerState.OPEN


def test_breaker_rejects_calls_while_open():
    """Test breaker rejects calls while open."""
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=60, clock=clock)

    breaker.record_failure("model-a")
    breaker.record_failure("model-a")

    assert not breaker.is_available("model-a")


def test_breaker_half_open_after_cooldown():
    """Test breaker goes half-open after cooldown."""
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=60, clock=clock)

    # Open the breaker
    breaker.record_failure("model-a")
    breaker.record_failure("model-a")
    assert not breaker.is_available("model-a")

    # Advance time past cooldown
    clock.advance(61)

    # Should now be half-open (available)
    assert breaker.is_available("model-a")
    status = breaker.get_status("model-a")
    assert status.state == BreakerState.HALF_OPEN


def test_breaker_closes_on_success():
    """Test breaker closes on successful call."""
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=60, clock=clock)

    # Open the breaker
    breaker.record_failure("model-a")
    breaker.record_failure("model-a")

    # Wait for cooldown
    clock.advance(61)
    assert breaker.is_available("model-a")

    # Record success
    breaker.record_success("model-a")

    status = breaker.get_status("model-a")
    assert status.state == BreakerState.CLOSED
    assert status.failure_count == 0


def test_breaker_reopens_on_half_open_failure():
    """Test breaker reopens if call fails in half-open state."""
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=60, clock=clock)

    # Open the breaker
    breaker.record_failure("model-a")
    breaker.record_failure("model-a")

    # Wait for cooldown -> half-open
    clock.advance(61)
    assert breaker.is_available("model-a")

    # Fail again -> should reopen
    breaker.record_failure("model-a")

    status = breaker.get_status("model-a")
    assert status.state == BreakerState.OPEN
    assert not breaker.is_available("model-a")
