"""Tests for response cache."""

from modelgate.cache import ResponseCache


class FakeClock:
    """Fake clock for testing."""

    def __init__(self):
        self.time = 0.0

    def __call__(self):
        return self.time

    def advance(self, seconds: float):
        self.time += seconds


def test_cache_hit_on_identical_request():
    """Test cache returns response for identical request."""
    cache = ResponseCache(max_size=10, ttl_seconds=60)

    request = {"model": "test", "messages": [{"role": "user", "content": "hello"}]}
    response = {"id": "test-123", "content": "response"}

    # First call - miss
    assert cache.get(request) is None

    # Store response
    cache.put(request, response)

    # Second call - hit
    cached = cache.get(request)
    assert cached == response


def test_cache_miss_on_different_temperature():
    """Test cache misses when temperature differs."""
    cache = ResponseCache(max_size=10, ttl_seconds=60)

    request1 = {"model": "test", "messages": [], "temperature": 0.7}
    request2 = {"model": "test", "messages": [], "temperature": 0.9}
    response = {"id": "test-123"}

    cache.put(request1, response)

    # Different temperature -> miss
    assert cache.get(request2) is None


def test_cache_expiry_after_ttl():
    """Test entries expire after TTL."""
    clock = FakeClock()
    cache = ResponseCache(max_size=10, ttl_seconds=60, clock=clock)

    request = {"model": "test", "messages": []}
    response = {"id": "test-123"}

    cache.put(request, response)

    # Within TTL - hit
    clock.advance(30)
    assert cache.get(request) == response

    # After TTL - miss
    clock.advance(31)
    assert cache.get(request) is None


def test_lru_eviction():
    """Test LRU eviction when at capacity."""
    cache = ResponseCache(max_size=2, ttl_seconds=60)

    req1 = {"model": "test", "id": 1}
    req2 = {"model": "test", "id": 2}
    req3 = {"model": "test", "id": 3}

    resp1 = {"content": "1"}
    resp2 = {"content": "2"}
    resp3 = {"content": "3"}

    # Fill cache
    cache.put(req1, resp1)
    cache.put(req2, resp2)

    # Both should be cached
    assert cache.get(req1) == resp1
    assert cache.get(req2) == resp2

    # Add third - should evict first (LRU)
    cache.put(req3, resp3)

    # req1 should be evicted, req2 and req3 cached
    assert cache.get(req1) is None
    assert cache.get(req2) == resp2
    assert cache.get(req3) == resp3


def test_cache_update_moves_to_end():
    """Test that accessing an entry moves it to end (LRU)."""
    cache = ResponseCache(max_size=2, ttl_seconds=60)

    req1 = {"model": "test", "id": 1}
    req2 = {"model": "test", "id": 2}
    req3 = {"model": "test", "id": 3}

    cache.put(req1, {"content": "1"})
    cache.put(req2, {"content": "2"})

    # Access req1 (moves to end)
    cache.get(req1)

    # Add req3 - should evict req2 (oldest)
    cache.put(req3, {"content": "3"})

    assert cache.get(req1) is not None
    assert cache.get(req2) is None
    assert cache.get(req3) is not None
