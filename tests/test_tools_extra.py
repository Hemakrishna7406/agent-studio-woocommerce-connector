"""Additional tool coverage: single-resource reads, search, health, streaming."""

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

PRODUCT = {
    "id": 5, "name": "Widget", "sku": "W-1", "type": "simple", "status": "publish",
    "price": "10", "regular_price": "12", "sale_price": "", "manage_stock": True,
    "stock_status": "instock", "stock_quantity": 7, "categories": [{"name": "Cat"}],
    "permalink": "https://demo.example.com/?p=5", "date_modified_gmt": "2026-01-01T00:00:00",
}

CUSTOMER = {
    "id": 7, "email": "a@b.com", "first_name": "A", "last_name": "B",
    "orders_count": 3, "total_spent": "100", "date_created_gmt": "2026-01-01T00:00:00",
}


def _client(config, responses):
    return WooCommerceClient(config, session=FakeSession(responses))


def test_get_order(config):
    c = _client(config, [FakeResponse(payload=ORDER)])
    assert tools.get_order(c, 101)["order"]["id"] == 101


def test_get_product(config):
    c = _client(config, [FakeResponse(payload=PRODUCT)])
    out = tools.get_product(c, 5)["product"]
    assert out["sku"] == "W-1"
    assert out["categories"] == ["Cat"]


def test_get_customer(config):
    c = _client(config, [FakeResponse(payload=CUSTOMER)])
    assert tools.get_customer(c, 7)["customer"]["orders_count"] == 3


def test_search_products_by_sku(config):
    c = _client(config, [FakeResponse(payload=[PRODUCT], headers={"X-WP-Total": "1", "X-WP-TotalPages": "1"})])
    out = tools.search_products(c, sku="W-1")
    assert out["products"][0]["id"] == 5
    assert c.session.calls[0]["params"]["sku"] == "W-1"


def test_list_orders_streams_all_pages(config):
    c = _client(
        config,
        [
            FakeResponse(payload=[ORDER], headers={"X-WP-TotalPages": "2"}),
            FakeResponse(payload=[{**ORDER, "id": 102}], headers={"X-WP-TotalPages": "2"}),
        ],
    )
    out = tools.list_orders(c, all_pages=True)
    assert out["count"] == 2
    assert [o["id"] for o in out["orders"]] == [101, 102]


def test_health_check_ok(config):
    c = _client(config, [FakeResponse(payload=[PRODUCT])])
    assert tools.health_check(c)["ok"] is True


def test_health_check_reports_failure(config):
    c = _client(config, [FakeResponse(status_code=401, text="bad key")])
    out = tools.health_check(c)
    assert out["ok"] is False
    assert "AuthError" in out["error"]
