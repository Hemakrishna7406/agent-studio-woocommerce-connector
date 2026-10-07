"""High-level, agent-facing operations built on the raw client.

These are plain functions (easy to unit-test) that the MCP server wraps.
Every function returns a JSON-serialisable dict — never a raw object.
"""

from __future__ import annotations

from typing import Any

from .models import normalize_customer, normalize_order, normalize_product
from .woocommerce_client import WooCommerceClient


def list_orders(
    client: WooCommerceClient,
    *,
    status: str | None = None,
    after: str | None = None,
    before: str | None = None,
    customer_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 50,
    all_pages: bool = False,
    max_items: int | None = None,
) -> dict[str, Any]:
    """List orders, optionally filtered. `after`/`before` are ISO-8601 dates."""
    params: dict[str, Any] = {}
    if status:
        params["status"] = status
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    if customer_id:
        params["customer"] = customer_id
    if search:
        params["search"] = search

    if all_pages:
        rows = [normalize_order(o) for o in client.paginate("orders", params, max_items=max_items)]
        return {
            "orders": rows,
            "count": len(rows),
            "truncated": max_items is not None and len(rows) >= max_items,
        }

    raw, meta = client.page("orders", params, page=page, per_page=per_page)
    return {"orders": [normalize_order(o) for o in raw], "pagination": meta}


def get_order(client: WooCommerceClient, order_id: int) -> dict[str, Any]:
    """Fetch a single order by id."""
    resp = client.get(f"orders/{int(order_id)}")
    return {"order": normalize_order(resp.json())}


def search_products(
    client: WooCommerceClient,
    *,
    query: str | None = None,
    sku: str | None = None,
    category: str | None = None,
    stock_status: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> dict[str, Any]:
    """Search the catalogue by free text, SKU, category or stock status."""
    params: dict[str, Any] = {}
    if query:
        params["search"] = query
    if sku:
        params["sku"] = sku
    if category:
        params["category"] = category
    if stock_status:
        params["stock_status"] = stock_status
    raw, meta = client.page("products", params, page=page, per_page=per_page)
    return {"products": [normalize_product(p) for p in raw], "pagination": meta}


def get_product(client: WooCommerceClient, product_id: int) -> dict[str, Any]:
    """Fetch a single product by id."""
    resp = client.get(f"products/{int(product_id)}")
    return {"product": normalize_product(resp.json())}


def list_inventory(
    client: WooCommerceClient,
    *,
    low_stock_threshold: int = 5,
    only_managed: bool = True,
    max_items: int = 500,
) -> dict[str, Any]:
    """Return products at or below `low_stock_threshold`.

    Streams the catalogue via the pagination primitive and caps at
    `max_items` so a huge store cannot blow up the agent's context.
    """
    rows: list[dict[str, Any]] = []
    scanned = 0
    for raw in client.paginate("products", {"status": "publish"}, max_items=max_items):
        scanned += 1
        p = normalize_product(raw)
        qty = p.get("stock_quantity")
        if only_managed and not p.get("manage_stock"):
            continue
        if isinstance(qty, int) and qty <= low_stock_threshold:
            rows.append(p)
    return {
        "low_stock": rows,
        "count": len(rows),
        "scanned": scanned,
        "threshold": low_stock_threshold,
        "truncated": scanned >= max_items,
    }


def get_customer(client: WooCommerceClient, customer_id: int) -> dict[str, Any]:
    """Fetch a single customer by id."""
    resp = client.get(f"customers/{int(customer_id)}")
    return {"customer": normalize_customer(resp.json())}


def health_check(client: WooCommerceClient) -> dict[str, Any]:
    """Cheap connectivity + auth probe the agent can call before a task."""
    try:
        client.get("products", {"per_page": 1})
        return {"ok": True, "store_url": client.cfg.store_url}
    except Exception as exc:  # surfaced to the agent, not raised
        return {"ok": False, "store_url": client.cfg.store_url, "error": f"{type(exc).__name__}: {exc}"}
