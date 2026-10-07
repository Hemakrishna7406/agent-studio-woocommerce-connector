"""Client behaviour: pagination, retries, and typed errors."""

from __future__ import annotations

import pytest

from connector import woocommerce_client as wc
from connector.errors import AuthError, RateLimitedError
from connector.woocommerce_client import WooCommerceClient
from tests.conftest import FakeResponse, FakeSession


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    # Retries should be instant in tests.
    monkeypatch.setattr(wc.time, "sleep", lambda *_: None)


def test_paginate_follows_total_pages(config):
    session = FakeSession(
        [
            FakeResponse(payload=[{"id": 1}, {"id": 2}], headers={"X-WP-TotalPages": "2", "X-WP-Total": "3"}),
            FakeResponse(payload=[{"id": 3}], headers={"X-WP-TotalPages": "2", "X-WP-Total": "3"}),
        ]
    )
    client = WooCommerceClient(config, session=session)
    ids = [row["id"] for row in client.paginate("orders", per_page=2)]
    assert ids == [1, 2, 3]
    assert session.calls[0]["params"]["page"] == 1
    assert session.calls[1]["params"]["page"] == 2


def test_paginate_respects_max_items(config):
    session = FakeSession(
        [FakeResponse(payload=[{"id": i} for i in range(5)], headers={"X-WP-TotalPages": "5"})]
    )
    client = WooCommerceClient(config, session=session)
    ids = [row["id"] for row in client.paginate("orders", per_page=5, max_items=3)]
    assert ids == [0, 1, 2]
    assert len(session.calls) == 1  # stopped early, never fetched page 2


def test_page_returns_metadata(config):
    session = FakeSession(
        [FakeResponse(payload=[{"id": 9}], headers={"X-WP-Total": "42", "X-WP-TotalPages": "3"})]
    )
    client = WooCommerceClient(config, session=session)
    items, meta = client.page("orders", page=2, per_page=20)
    assert items == [{"id": 9}]
    assert meta == {"page": 2, "per_page": 20, "total": 42, "total_pages": 3}


def test_retry_then_success_on_429(config):
    session = FakeSession(
        [
            FakeResponse(status_code=429, headers={"Retry-After": "1"}),
            FakeResponse(payload=[{"id": 1}], headers={"X-WP-TotalPages": "1"}),
        ]
    )
    client = WooCommerceClient(config, session=session)
    resp = client.get("orders")
    assert resp.status_code == 200
    assert len(session.calls) == 2


def test_429_exhausted_raises_rate_limited(config):
    session = FakeSession([FakeResponse(status_code=429) for _ in range(config.max_retries + 1)])
    client = WooCommerceClient(config, session=session)
    with pytest.raises(RateLimitedError):
        client.get("orders")


def test_401_raises_auth_error(config):
    session = FakeSession([FakeResponse(status_code=401, text="invalid key")])
    client = WooCommerceClient(config, session=session)
    with pytest.raises(AuthError):
        client.get("orders")
