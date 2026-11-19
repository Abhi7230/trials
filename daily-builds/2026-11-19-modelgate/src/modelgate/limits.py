"""Rate and budget limits with token bucket."""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""

    capacity: int
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float


@dataclass
class ApiKeyLimits:
    """Per-API-key limits."""

    daily_usd: float
    rpm_bucket: TokenBucket
    tpm_bucket: TokenBucket
    spent_today: float = 0.0
    day_start: float = 0.0


class LimitExceededError(Exception):
    """Rate or budget limit exceeded."""


class LimitsManager:
    """Manage rate and budget limits per API key."""

    def __init__(
        self,
        default_daily_usd: float,
        default_rpm: int,
        default_tpm: int,
        clock: Callable[[], float] | None = None,
    ):
        self.default_daily_usd = default_daily_usd
        self.default_rpm = default_rpm
        self.default_tpm = default_tpm
        self.clock = clock or self._default_clock
        self._limits: dict[str, ApiKeyLimits] = {}

    @staticmethod
    def _default_clock() -> float:
        """Default clock using time.time()."""
        import time  # noqa: PLC0415

        return time.time()

    def _get_or_create(self, api_key: str) -> ApiKeyLimits:
        """Get or create limits for an API key."""
        if api_key not in self._limits:
            now = self.clock()
            self._limits[api_key] = ApiKeyLimits(
                daily_usd=self.default_daily_usd,
                rpm_bucket=TokenBucket(
                    capacity=self.default_rpm,
                    tokens=float(self.default_rpm),
                    refill_rate=self.default_rpm / 60.0,
                    last_refill=now,
                ),
                tpm_bucket=TokenBucket(
                    capacity=self.default_tpm,
                    tokens=float(self.default_tpm),
                    refill_rate=self.default_tpm / 60.0,
                    last_refill=now,
                ),
                day_start=now,
            )
        return self._limits[api_key]

    def _refill_bucket(self, bucket: TokenBucket) -> None:
        """Refill token bucket based on elapsed time."""
        now = self.clock()
        elapsed = now - bucket.last_refill
        refill = elapsed * bucket.refill_rate
        bucket.tokens = min(bucket.capacity, bucket.tokens + refill)
        bucket.last_refill = now

    def _reset_daily_if_needed(self, limits: ApiKeyLimits) -> None:
        """Reset daily budget if 24 hours have passed."""
        now = self.clock()
        if now - limits.day_start >= 86400:  # 24 hours
            limits.spent_today = 0.0
            limits.day_start = now

    def check_and_consume(self, api_key: str, tokens: int, cost_usd: float) -> None:
        """Check limits and consume if available."""
        limits = self._get_or_create(api_key)
        self._reset_daily_if_needed(limits)
        self._refill_bucket(limits.rpm_bucket)
        self._refill_bucket(limits.tpm_bucket)

        # Check daily budget
        if limits.spent_today + cost_usd > limits.daily_usd:
            raise LimitExceededError("Daily budget exceeded")

        # Check RPM
        if limits.rpm_bucket.tokens < 1:
            raise LimitExceededError("Rate limit exceeded (requests per minute)")

        # Check TPM
        if limits.tpm_bucket.tokens < tokens:
            raise LimitExceededError("Rate limit exceeded (tokens per minute)")

        # Consume tokens
        limits.rpm_bucket.tokens -= 1
        limits.tpm_bucket.tokens -= tokens
        limits.spent_today += cost_usd

    def get_remaining_budget(self, api_key: str) -> float:
        """Get remaining daily budget."""
        limits = self._get_or_create(api_key)
        self._reset_daily_if_needed(limits)
        return limits.daily_usd - limits.spent_today
