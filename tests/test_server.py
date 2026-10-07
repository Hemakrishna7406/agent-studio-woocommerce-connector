"""MCP server: tools are registered and delegate to the connector core."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp", reason="MCP SDK is a runtime dependency (see requirements.txt)")

import mcp_server.server as server  # noqa: E402
from connector.woocommerce_client import WooCommerceClient  # noqa: E402
from tests.conftest import FakeResponse, FakeSession  # noqa: E402

TOOL_NAMES = [
    "health_check",
    "list_orders",
    "get_order",
    "search_products",
    "get_product",
    "list_inventory",
    "get_customer",
]


def test_all_tools_are_registered():
    for name in TOOL_NAMES:
        assert callable(getattr(server, name)), f"{name} is not exposed"


def _patch_client(monkeypatch, config, responses):
    client = WooCommerceClient(config, session=FakeSession(responses))
    monkeypatch.setattr(server, "get_client", lambda: client)
    return client


def test_server_health_check(monkeypatch, config):
    _patch_client(monkeypatch, config, [FakeResponse(payload=[{"id": 1}])])
    assert server.health_check()["ok"] is True


def test_server_list_orders(monkeypatch, config):
    order = {
        "id": 1, "number": "1", "status": "processing", "currency": "INR", "total": "10",
        "billing": {}, "line_items": [],
    }
    _patch_client(monkeypatch, config, [FakeResponse(payload=[order], headers={"X-WP-TotalPages": "1"})])
    out = server.list_orders(status="processing")
    assert out["orders"][0]["id"] == 1


def test_server_get_order(monkeypatch, config):
    order = {"id": 9, "number": "9", "status": "completed", "currency": "INR", "total": "5",
             "billing": {}, "line_items": []}
    _patch_client(monkeypatch, config, [FakeResponse(payload=order)])
    assert server.get_order(9)["order"]["id"] == 9
