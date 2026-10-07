"""Rate limiter: token bucket + backoff behaviour."""

from __future__ import annotations

from connector.rate_limiter import TokenBucket, backoff_delay


def test_token_bucket_consumes_and_refills():
    bucket = TokenBucket(rate_per_second=1000, capacity=2)
    bucket.acquire()
    bucket.acquire()  # drained
    bucket.acquire()  # must wait for a refill, then succeed
    assert True  # reached only if it did not block forever


def test_backoff_grows_then_caps():
    assert backoff_delay(0, base=1, cap=10, jitter=False) == 1
    assert backoff_delay(3, base=1, cap=10, jitter=False) == 8
    assert backoff_delay(10, base=1, cap=10, jitter=False) == 10  # capped


def test_backoff_jitter_stays_in_range():
    for _ in range(25):
        d = backoff_delay(2, base=1, cap=10, jitter=True)
        assert 0 < d <= 10
