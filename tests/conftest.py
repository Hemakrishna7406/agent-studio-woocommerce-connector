"""Shared test fixtures: a fake requests.Session so tests never hit the network."""

from __future__ import annotations

import json
from typing import Any

import pytest

from connector.config import Config


class FakeResponse:
    def __init__(self, status_code: int = 200, payload: Any = None, headers: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload if payload is not None else []
        self.headers = headers or {}
        self.text = text or json.dumps(self._payload)

    def json(self) -> Any:
        return self._payload


class FakeSession:
    """Mimics the slice of requests.Session the client actually uses."""

    def __init__(self, responses: list[Any]):
        self._responses = list(responses)
        self.calls: list[dict] = []
        self.auth = None
        self.headers: dict = {}

    def request(self, method: str, url: str, params=None, timeout=None, verify=None, **kw) -> Any:
        # Copy params: the client reuses one dict across pages, so storing a
        # live reference would make every recorded call show the final page.
        self.calls.append({"method": method, "url": url, "params": dict(params) if params else params})
        if not self._responses:
            raise AssertionError("FakeSession ran out of queued responses")
        item = self._responses.pop(0)
        if callable(item):
            return item(method, url, params)
        return item


@pytest.fixture
def config() -> Config:
    return Config(
        store_url="https://demo.example.com",
        consumer_key="ck_test",
        consumer_secret="cs_test",
        requests_per_second=10_000,  # effectively no throttling in tests
        max_retries=3,
    )
