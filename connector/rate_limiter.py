"""Client-side politeness (token bucket) + retry backoff helpers.

Two layers of protection:
  1. TokenBucket — smooths our own outbound request rate so we never hammer
     the store in the first place.
  2. backoff_delay — exponential backoff with jitter, used when the store
     (or its CDN/WAF) pushes back with 429/5xx.
"""

from __future__ import annotations

import random
import threading
import time


class TokenBucket:
    """Thread-safe token bucket rate limiter."""

    def __init__(self, rate_per_second: float, capacity: float | None = None):
        self.rate = float(rate_per_second)
        self.capacity = float(capacity if capacity is not None else max(1.0, rate_per_second))
        self._tokens = self.capacity
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: float = 1.0) -> None:
        """Block until `tokens` are available, then consume them."""
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._last
                self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
                self._last = now
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                deficit = tokens - self._tokens
                wait = deficit / self.rate
            time.sleep(wait)


def backoff_delay(attempt: int, base: float = 0.5, cap: float = 30.0, jitter: bool = True) -> float:
    """Exponential backoff with optional full jitter.

    attempt is 0-based: 0 -> ~base, 1 -> ~2*base, 2 -> ~4*base, ... capped.
    """
    delay = min(cap, base * (2 ** attempt))
    if jitter:
        delay *= 0.5 + random.random() / 2.0
    return delay
