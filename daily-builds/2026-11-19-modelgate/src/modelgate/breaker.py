"""Circuit breaker implementation."""

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class BreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class BreakerStatus:
    """Circuit breaker status."""

    state: BreakerState
    failure_count: int
    last_failure_time: float | None


class CircuitBreaker:
    """Per-model circuit breaker."""

    def __init__(
        self,
        failure_threshold: int,
        cooldown_seconds: float,
        clock: Callable[[], float] | None = None,
    ):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.clock = clock or self._default_clock
        self._breakers: dict[str, BreakerStatus] = {}

    @staticmethod
    def _default_clock() -> float:
        """Default clock using time.time()."""
        import time

        return time.time()

    def get_status(self, model_id: str) -> BreakerStatus:
        """Get breaker status for a model."""
        if model_id not in self._breakers:
            self._breakers[model_id] = BreakerStatus(
                state=BreakerState.CLOSED, failure_count=0, last_failure_time=None
            )
        return self._breakers[model_id]

    def is_available(self, model_id: str) -> bool:
        """Check if model is available (breaker not open)."""
        status = self.get_status(model_id)

        if status.state == BreakerState.CLOSED:
            return True

        if status.state == BreakerState.OPEN:
            # Check if cooldown has passed
            if (
                status.last_failure_time is not None
                and self.clock() - status.last_failure_time >= self.cooldown_seconds
            ):
                # Transition to half-open
                status.state = BreakerState.HALF_OPEN
                return True
            return False

        # HALF_OPEN
        return True

    def record_success(self, model_id: str) -> None:
        """Record successful call."""
        status = self.get_status(model_id)
        status.state = BreakerState.CLOSED
        status.failure_count = 0

    def record_failure(self, model_id: str) -> None:
        """Record failed call."""
        status = self.get_status(model_id)
        now = self.clock()

        if status.state == BreakerState.HALF_OPEN:
            # Half-open failure -> reopen
            status.state = BreakerState.OPEN
            status.last_failure_time = now
            return

        # Closed state
        status.failure_count += 1
        status.last_failure_time = now

        if status.failure_count >= self.failure_threshold:
            status.state = BreakerState.OPEN
