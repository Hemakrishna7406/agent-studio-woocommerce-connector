# MCP tool specification

The connector exposes seven read-only tools. Each is defined here with its
input schema and return shape so an Agent Studio agent (or any MCP host) can
call them without guessing.

Transport: MCP (`stdio` by default, `streamable-http` optional).
All tools return JSON objects. Errors are returned as typed `WooCommerceError`
subclasses; `health_check` never raises (it reports `{"ok": false, ...}`).

---

## 1. `health_check`

Connectivity + credential probe.

- **Input:** none.
- **Returns:** `{ "ok": bool, "store_url": str, "error"?: str }`

---

## 2. `list_orders`

List orders with optional filters.

- **Input**

| field | type | default | notes |
|---|---|---|---|
| `status` | string | null | pending, processing, completed, refunded, cancelled, failed |
| `after` | string | null | ISO-8601, e.g. `2026-01-01T00:00:00` |
| `before` | string | null | ISO-8601 |
| `customer_id` | integer | null | filter to one customer |
| `search` | string | null | matches order/customer fields |
| `page` | integer | 1 | 1-based |
| `per_page` | integer | 50 | max 100 |

- **Returns:** `{ "orders": [Order], "pagination": {page, per_page, total, total_pages} }`

`Order` = `{id, number, status, currency, total, date_created, date_paid,
customer_id, payment_method, payment_method_title, customer_name,
customer_email, items: [{product_id, name, quantity, total}]}`

---

## 3. `get_order`

- **Input:** `{ "order_id": integer }`
- **Returns:** `{ "order": Order }`

---

## 4. `search_products`

Search the catalogue.

- **Input**

| field | type | default | notes |
|---|---|---|---|
| `query` | string | null | free text |
| `sku` | string | null | exact SKU |
| `category` | string | null | category id or slug |
| `stock_status` | string | null | instock / outofstock / onbackorder |
| `page` | integer | 1 | |
| `per_page` | integer | 50 | max 100 |

- **Returns:** `{ "products": [Product], "pagination": {...} }`

`Product` = `{id, name, sku, type, status, price, regular_price, sale_price,
manage_stock, stock_status, stock_quantity, categories, permalink, date_modified}`

---

## 5. `get_product`

- **Input:** `{ "product_id": integer }`
- **Returns:** `{ "product": Product }`

---

## 6. `list_inventory`

Products at or below a stock threshold.

- **Input**

| field | type | default | notes |
|---|---|---|---|
| `low_stock_threshold` | integer | 5 | inclusive |
| `only_managed` | boolean | true | skip products not stock-managed |
| `max_items` | integer | 500 | scan cap |

- **Returns:** `{ "low_stock": [Product], "count": int, "scanned": int, "threshold": int, "truncated": bool }`

---

## 7. `get_customer`

- **Input:** `{ "customer_id": integer }`
- **Returns:** `{ "customer": {id, email, first_name, last_name, orders_count, total_spent, date_created} }`

---

## Design rules

1. **Read-only.** No tool mutates the store.
2. **Bounded.** Every list tool paginates and can be capped, so no single call
   can exhaust the agent's context or the store's rate budget.
3. **Normalised.** Raw WooCommerce payloads are projected to the shapes above.
4. **Typed errors.** The agent receives `AuthError`, `NotFoundError`,
   `RateLimitedError`, or `UpstreamError`, and can decide how to react.
