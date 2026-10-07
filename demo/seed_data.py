"""Seed a local demo store with sample products and orders.

Uses a Read/Write API key (seeding writes; the connector itself is read-only).
Never point this at a real merchant store.

    WC_STORE_URL=http://localhost:8080 WC_CONSUMER_KEY=ck_... \
    WC_CONSUMER_SECRET=cs_... python demo/seed_data.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

BASE = (os.environ.get("WC_STORE_URL") or "").rstrip("/") + "/wp-json/wc/v3"
AUTH = HTTPBasicAuth(os.environ.get("WC_CONSUMER_KEY", ""), os.environ.get("WC_CONSUMER_SECRET", ""))

PRODUCTS = [
    {"name": "Aurora Bluetooth Speaker", "regular_price": "2999", "sku": "AUD-001", "manage_stock": True, "stock_quantity": 40},
    {"name": "Nimbus Wireless Earbuds", "regular_price": "1999", "sku": "AUD-002", "manage_stock": True, "stock_quantity": 3},
    {"name": "Pulse Smartwatch", "regular_price": "5999", "sku": "WEA-001", "manage_stock": True, "stock_quantity": 0},
    {"name": "Vega Power Bank 20000mAh", "regular_price": "1799", "sku": "ACC-001", "manage_stock": True, "stock_quantity": 120},
    {"name": "Orbit Laptop Stand", "regular_price": "899", "sku": "ACC-002", "manage_stock": True, "stock_quantity": 2},
    {"name": "Zenith Mechanical Keyboard", "regular_price": "4499", "sku": "ACC-003", "manage_stock": True, "stock_quantity": 15},
]


def post(path: str, payload: dict) -> dict:
    r = requests.post(f"{BASE}/{path}", json=payload, auth=AUTH, timeout=30)
    r.raise_for_status()
    return r.json()


def main() -> None:
    if not os.environ.get("WC_STORE_URL"):
        raise SystemExit("Set WC_STORE_URL, WC_CONSUMER_KEY, WC_CONSUMER_SECRET first.")

    print("Creating products ...")
    ids = []
    for p in PRODUCTS:
        created = post("products", p)
        ids.append(created["id"])
        print(f"  #{created['id']}  {created['name']}")

    print("Creating orders ...")
    for i in range(10):
        payload = {
            "payment_method": "razorpay" if i % 2 == 0 else "cod",
            "set_paid": i % 3 == 0,
            "status": ["processing", "completed", "pending"][i % 3],
            "billing": {
                "first_name": f"Customer{i}",
                "last_name": "Demo",
                "email": f"customer{i}@example.com",
                "address_1": "1 Demo Road",
                "city": "Bangalore",
                "country": "IN",
            },
            "line_items": [{"product_id": ids[i % len(ids)], "quantity": 1 + (i % 2)}],
        }
        created = post("orders", payload)
        print(f"  order #{created['number']}  {created['status']}")

    print("Seeding complete.")


if __name__ == "__main__":
    main()
