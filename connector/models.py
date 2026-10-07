"""Normalisers: map raw WooCommerce payloads to small, agent-friendly dicts.

WooCommerce objects are large and verbose. Returning the raw payload would
burn the agent's context window and leak fields it should not rely on. We
project each resource down to a stable, documented shape.
"""

from __future__ import annotations

from typing import Any


def _first(value: Any) -> Any:
    return value[0] if isinstance(value, list) and value else value


def normalize_order(o: dict) -> dict:
    billing = o.get("billing") or {}
    return {
        "id": o.get("id"),
        "number": o.get("number"),
        "status": o.get("status"),
        "currency": o.get("currency"),
        "total": o.get("total"),
        "date_created": o.get("date_created_gmt") or o.get("date_created"),
        "date_paid": o.get("date_paid_gmt") or o.get("date_paid"),
        "customer_id": o.get("customer_id"),
        "payment_method": o.get("payment_method"),
        "payment_method_title": o.get("payment_method_title"),
        "items": [
            {
                "product_id": li.get("product_id"),
                "name": li.get("name"),
                "quantity": li.get("quantity"),
                "total": li.get("total"),
            }
            for li in (o.get("line_items") or [])
        ],
        "customer_name": f"{billing.get('first_name','')} {billing.get('last_name','')}".strip() or None,
        "customer_email": billing.get("email"),
    }


def normalize_product(p: dict) -> dict:
    stock_qty = p.get("stock_quantity")
    return {
        "id": p.get("id"),
        "name": p.get("name"),
        "sku": p.get("sku"),
        "type": p.get("type"),
        "status": p.get("status"),
        "price": p.get("price"),
        "regular_price": p.get("regular_price"),
        "sale_price": p.get("sale_price") or None,
        "currency": None,  # filled by caller when known
        "manage_stock": p.get("manage_stock"),
        "stock_status": p.get("stock_status"),
        "stock_quantity": stock_qty,
        "categories": [c.get("name") for c in (p.get("categories") or [])],
        "permalink": p.get("permalink"),
        "date_modified": p.get("date_modified_gmt") or p.get("date_modified"),
    }


def normalize_customer(c: dict) -> dict:
    return {
        "id": c.get("id"),
        "email": c.get("email"),
        "first_name": c.get("first_name"),
        "last_name": c.get("last_name"),
        "orders_count": c.get("orders_count"),
        "total_spent": c.get("total_spent"),
        "date_created": c.get("date_created_gmt") or c.get("date_created"),
    }
