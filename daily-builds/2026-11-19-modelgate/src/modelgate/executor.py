"""Request execution with fallback and circuit breaker."""

import asyncio
from dataclasses import dataclass
from typing import Any

from modelgate.breaker import CircuitBreaker
from modelgate.catalog import Model
from modelgate.providers.base import Provider, ProviderError, ProviderResponse


@dataclass
class ExecutionResult:
    """Result of executing a request."""

    response: ProviderResponse
    model: Model
    attempts: int
    errors: list[str]


class ExecutionError(Exception):
    """All attempts failed."""

    def __init__(self, message: str, attempts: int, errors: list[str]):
        super().__init__(message)
        self.attempts = attempts
        self.errors = errors


class Executor:
    """Execute requests with fallback chain."""

    def __init__(
        self,
        provider: Provider,
        breaker: CircuitBreaker,
        max_attempts: int,
        timeout: float,
    ):
        self.provider = provider
        self.breaker = breaker
        self.max_attempts = max_attempts
        self.timeout = timeout

    def execute(self, models: list[Model], request: dict[str, Any]) -> ExecutionResult:
        """Execute request with fallback chain."""
        errors: list[str] = []
        attempts = 0

        for model in models[: self.max_attempts]:
            # Skip if breaker is open
            if not self.breaker.is_available(model.id):
                errors.append(f"{model.id}: circuit breaker open")
                continue

            attempts += 1

            try:
                # Execute with timeout
                response = self._execute_with_timeout(model, request)
                self.breaker.record_success(model.id)
                return ExecutionResult(
                    response=response,
                    model=model,
                    attempts=attempts,
                    errors=errors,
                )

            except ProviderError as e:
                error_msg = f"{model.id}: {e}"
                errors.append(error_msg)
                self.breaker.record_failure(model.id)

                if not e.retriable:
                    # Non-retriable error, stop fallback
                    raise ExecutionError(
                        f"Non-retriable error: {e}", attempts=attempts, errors=errors
                    ) from e

            except TimeoutError:
                error_msg = f"{model.id}: timeout"
                errors.append(error_msg)
                self.breaker.record_failure(model.id)

        # All attempts exhausted
        raise ExecutionError(
            f"All {attempts} attempts failed",
            attempts=attempts,
            errors=errors,
        )

    def _execute_with_timeout(self, model: Model, request: dict[str, Any]) -> ProviderResponse:
        """Execute with timeout."""
        try:
            # Run provider call with timeout
            result = asyncio.wait_for(
                asyncio.to_thread(self.provider.complete, model.id, request),
                timeout=self.timeout,
            )
            return asyncio.run(result)
        except asyncio.TimeoutError as e:
            raise TimeoutError(f"Request timeout after {self.timeout}s") from e
