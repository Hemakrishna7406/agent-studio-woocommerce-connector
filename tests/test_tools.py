"""Tool layer: normalisation and inventory filtering."""

from __future__ import annotations

from connector import tools
from connector.woocommerce_client import WooCommerceClient
from tests.conftest import FakeResponse, FakeSession

ORDER = {
    "id": 101,
    "number": "101",
    "status": "processing",
    "currency": "INR",
    "total": "1499.00",
    "date_created_gmt": "2026-09-01T10:00:00",
    "customer_id": 7,
    "billing": {"first_name": "Asha", "last_name": "Rao", "email": "asha@example.com"},
    "line_items": [{"product_id": 5, "name": "Widget", "quantity": 2, "total": "1499.00"}],
}


def test_list_orders_normalises_and_returns_meta(config):
    session = FakeSession(
        [FakeResponse(payload=[ORDER], headers={"X-WP-Total": "1", "X-WP-TotalPages": "1"})]
    )
    client = WooCommerceClient(config, session=session)
    out = tools.list_orders(client, status="processing")
    assert out["pagination"]["total"] == 1
    order = out["orders"][0]
    assert order["id"] == 101
    assert order["customer_name"] == "Asha Rao"
    assert order["items"][0]["name"] == "Widget"
    assert session.calls[0]["params"]["status"] == "processing"


def test_list_inventory_filters_low_stock(config):
    products = [
        {"id": 1, "name": "Low", "manage_stock": True, "stock_quantity": 2, "stock_status": "instock", "categories": []},
        {"id": 2, "name": "Plenty", "manage_stock": True, "stock_quantity": 50, "stock_status": "instock", "categories": []},
        {"id": 3, "name": "Unmanaged", "manage_stock": False, "stock_quantity": None, "stock_status": "instock", "categories": []},
    ]
    session = FakeSession([FakeResponse(payload=products, headers={"X-WP-TotalPages": "1"})])
    client = WooCommerceClient(config, session=session)
    out = tools.list_inventory(client, low_stock_threshold=5)
    assert out["count"] == 1
    assert out["low_stock"][0]["id"] == 1
