"""Clock abstraction for testability."""

from datetime import datetime, timezone
from typing import Protocol


class Clock(Protocol):
    """Clock interface for dependency injection."""

    def now(self) -> datetime:
        """Return current UTC datetime."""
        ...


class SystemClock:
    """Real system clock."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FixedClock:
    """Fixed clock for testing."""

    def __init__(self, current: datetime | None = None):
        self._current = current or datetime.now(timezone.utc)

    def now(self) -> datetime:
        return self._current

    def advance(self, **kwargs) -> None:
        """Advance time by timedelta kwargs."""
        from datetime import timedelta
        self._current += timedelta(**kwargs)

    def set(self, dt: datetime) -> None:
        """Set the clock to a specific time."""
        self._current = dt
