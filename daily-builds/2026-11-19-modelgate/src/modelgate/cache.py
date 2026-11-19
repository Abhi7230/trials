"""Response cache with LRU and TTL."""

import hashlib
import json
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class CacheEntry:
    """Cached response entry."""

    response: dict[str, Any]
    timestamp: float


class ResponseCache:
    """LRU cache with TTL for responses."""

    def __init__(
        self,
        max_size: int,
        ttl_seconds: float,
        clock: Callable[[], float] | None = None,
    ):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.clock = clock or self._default_clock
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

    @staticmethod
    def _default_clock() -> float:
        """Default clock using time.time()."""
        import time

        return time.time()

    def _normalize_request(self, request: dict[str, Any]) -> str:
        """Create cache key from request."""
        # Normalize: sort keys and create deterministic JSON
        normalized = json.dumps(request, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode()).hexdigest()

    def get(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Get cached response if available and not expired."""
        key = self._normalize_request(request)

        if key not in self._cache:
            return None

        entry = self._cache[key]
        now = self.clock()

        # Check TTL
        if now - entry.timestamp > self.ttl_seconds:
            del self._cache[key]
            return None

        # Move to end (LRU)
        self._cache.move_to_end(key)
        return entry.response

    def put(self, request: dict[str, Any], response: dict[str, Any]) -> None:
        """Store response in cache."""
        key = self._normalize_request(request)
        now = self.clock()

        # Evict oldest if at capacity
        if key not in self._cache and len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)

        self._cache[key] = CacheEntry(response=response, timestamp=now)
        self._cache.move_to_end(key)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
