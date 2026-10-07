"""Offline end-to-end demo — a mock WooCommerce store + the REAL connector.

Why this exists: a reviewer should be able to see the connector work in
seconds, with no Docker, no WordPress, no API keys and no network. This
script starts a tiny in-process HTTP server that speaks the WooCommerce REST
shape (Basic auth, X-WP-TotalPages pagination, 429 once), points the real
connector at it, and runs the real tools end to end.

Run:
    python demo/demo_offline.py
"""

from __future__ import annotations

import base64
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from connector import tools  # noqa: E402
from connector.config import Config  # noqa: E402
from connector.woocommerce_client import WooCommerceClient  # noqa: E402

CK, CS = "ck_demo", "cs_demo"
EXPECTED_AUTH = "Basic " + base64.b64encode(f"{CK}:{CS}".encode()).decode()

ORDERS = [
    {
        "id": 1001 + i,
        "number": str(1001 + i),
        "status": ["processing", "completed", "pending"][i % 3],
        "currency": "INR",
        "total": f"{999 + i * 100}.00",
        "date_created_gmt": f"2026-09-{10 + i:02d}T09:00:00",
        "customer_id": 500 + i,
        "billing": {"first_name": f"Cust{i}", "last_name": "Demo", "email": f"cust{i}@example.com"},
        "line_items": [{"product_id": 200 + i, "name": f"Item {i}", "quantity": 1 + i % 3, "total": f"{999 + i * 100}.00"}],
    }
    for i in range(7)
]

PRODUCTS = [
    {"id": 200 + i, "name": f"Product {i}", "sku": f"SKU-{i:03d}", "type": "simple",
     "status": "publish", "price": f"{199 + i * 50}.00", "regular_price": f"{199 + i * 50}.00",
     "sale_price": "", "manage_stock": True, "stock_status": "instock",
     "stock_quantity": [1, 40, 3, 0, 12, 2, 88][i], "categories": [{"name": "Demo"}],
     "permalink": f"https://demo.example.com/?p={200 + i}", "date_modified_gmt": "2026-09-15T00:00:00"}
    for i in range(7)
]

_request_counter = {"n": 0}


def _paginate(rows: list, q: dict) -> tuple[list, dict]:
    per_page = int((q.get("per_page") or ["50"])[0])
    page = int((q.get("page") or ["1"])[0])
    total = len(rows)
    total_pages = max(1, -(-total // per_page))
    start = (page - 1) * per_page
    return rows[start:start + per_page], {"X-WP-Total": str(total), "X-WP-TotalPages": str(total_pages)}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.headers.get("Authorization", "") != EXPECTED_AUTH:
            return self._send(401, {"code": "woocommerce_rest_cannot_view", "message": "Unauthorized"})

        _request_counter["n"] += 1
        # Simulate the store rate-limiting us exactly once, to exercise retries.
        if _request_counter["n"] == 2:
            return self._send(429, {"code": "too_many_requests"}, {"Retry-After": "0"})

        parsed = urlparse(self.path)
        q = parse_qs(parsed.query)
        path = parsed.path

        if path.endswith("/orders"):
            rows = ORDERS
            if q.get("status"):
                rows = [o for o in rows if o["status"] == q["status"][0]]
            rows, headers = _paginate(rows, q)
            return self._send(200, rows, headers)
        if path.endswith("/products"):
            rows = PRODUCTS
            if q.get("search"):
                needle = q["search"][0].lower()
                rows = [p for p in rows if needle in p["name"].lower()]
            if q.get("sku"):
                rows = [p for p in rows if p["sku"] == q["sku"][0]]
            if q.get("stock_status"):
                rows = [p for p in rows if p["stock_status"] == q["stock_status"][0]]
            rows, headers = _paginate(rows, q)
            return self._send(200, rows, headers)
        return self._send(404, {"code": "woocommerce_rest_shop_order_invalid_id", "message": "Not found"})

    def _send(self, code: int, payload, headers: dict | None = None):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # silence
        pass


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8899), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    cfg = Config(store_url="http://127.0.0.1:8899", consumer_key=CK, consumer_secret=CS, requests_per_second=1000)
    client = WooCommerceClient(cfg)

    print("=" * 68)
    print("Agent Studio — WooCommerce connector · offline end-to-end demo")
    print("=" * 68)

    print("\n[1] health_check:", json.dumps(tools.health_check(client), indent=2))

    print("\n[2] list_orders(status='processing')")
    out = tools.list_orders(client, status="processing")
    for o in out["orders"]:
        print(f"    #{o['number']}  {o['status']:<11} {o['currency']} {o['total']:>8}  {o['customer_name']}")
    print("    pagination:", out["pagination"])

    print("\n[3] search_products(query='Product')")
    prods = tools.search_products(client, query="Product")["products"]
    print(f"    {len(prods)} products, first = {prods[0]['name']} @ {prods[0]['price']}")

    print("\n[4] list_inventory(low_stock_threshold=5)")
    inv = tools.list_inventory(client, low_stock_threshold=5)
    for p in inv["low_stock"]:
        print(f"    LOW: {p['name']:<12} qty={p['stock_quantity']}")
    print(f"    count={inv['count']} scanned={inv['scanned']}")

    server.shutdown()
    print("\nDone. (Note: request #2 was a simulated 429 — the client retried automatically.)")


if __name__ == "__main__":
    main()
