"""Agent Studio — WooCommerce connector, exposed as an MCP server.

Run:
    python -m mcp_server.server              # stdio (default, for MCP hosts)
    MCP_TRANSPORT=streamable-http python -m mcp_server.server

Tools are read-only. The agent gets typed, normalised results and typed
errors, so it can decide what to do instead of crashing on a raw 500.
"""

from __future__ import annotations

import os
from typing import Any

from connector.config import Config
from connector.woocommerce_client import WooCommerceClient
from connector import tools

# --- MCP SDK compatibility -------------------------------------------------
# mcp>=2 exposes MCPServer (formerly FastMCP); mcp<2 exposes FastMCP.
try:  # pragma: no cover - import shim
    from mcp.server.mcpserver import MCPServer as _Server  # type: ignore
except Exception:  # pragma: no cover
    from mcp.server.fastmcp import FastMCP as _Server  # type: ignore


mcp = _Server(
    name="woocommerce-connector",
    instructions=(
        "Read-only access to a WooCommerce store's orders, products, inventory "
        "and customers. Start with health_check, then use the read tools. "
        "Never expect write operations — this connector cannot modify data."
    ),
)

_client: WooCommerceClient | None = None


def get_client() -> WooCommerceClient:
    """Lazily build the client so `--help`/import never needs secrets."""
    global _client
    if _client is None:
        cfg = Config.from_env()
        cfg.validate()
        _client = WooCommerceClient(cfg)
    return _client


# --- Tools -----------------------------------------------------------------

@mcp.tool()
def health_check() -> dict:
    """Check connectivity and credentials against the configured store."""
    return tools.health_check(get_client())


@mcp.tool()
def list_orders(
    status: str | None = None,
    after: str | None = None,
    before: str | None = None,
    customer_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> dict:
    """List orders. `status` e.g. pending/processing/completed/refunded.

    `after`/`before` are ISO-8601 dates (e.g. 2026-01-01T00:00:00). `search`
    matches order/customer fields. Returns a page plus pagination metadata.
    """
    return tools.list_orders(
        get_client(),
        status=status,
        after=after,
        before=before,
        customer_id=customer_id,
        search=search,
        page=page,
        per_page=per_page,
    )


@mcp.tool()
def get_order(order_id: int) -> dict:
    """Fetch a single order (line items, status, totals) by id."""
    return tools.get_order(get_client(), order_id)


@mcp.tool()
def search_products(
    query: str | None = None,
    sku: str | None = None,
    category: str | None = None,
    stock_status: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> dict:
    """Search products by free text, SKU, category id/name, or stock status.

    `stock_status` is one of instock/outofstock/onbackorder.
    """
    return tools.search_products(
        get_client(),
        query=query,
        sku=sku,
        category=category,
        stock_status=stock_status,
        page=page,
        per_page=per_page,
    )


@mcp.tool()
def get_product(product_id: int) -> dict:
    """Fetch a single product by id (price, stock, categories)."""
    return tools.get_product(get_client(), product_id)


@mcp.tool()
def list_inventory(low_stock_threshold: int = 5, only_managed: bool = True, max_items: int = 500) -> dict:
    """List products at or below `low_stock_threshold` units.

    Scans the published catalogue via pagination, capped at `max_items`.
    """
    return tools.list_inventory(
        get_client(),
        low_stock_threshold=low_stock_threshold,
        only_managed=only_managed,
        max_items=max_items,
    )


@mcp.tool()
def get_customer(customer_id: int) -> dict:
    """Fetch a single customer by id (orders count, lifetime spend)."""
    return tools.get_customer(get_client(), customer_id)


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
