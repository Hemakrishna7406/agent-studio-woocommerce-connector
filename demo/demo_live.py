"""Live demo against a real (local) WooCommerce store.

    WC_STORE_URL=http://localhost:8080 WC_CONSUMER_KEY=ck_... \
    WC_CONSUMER_SECRET=cs_... python demo/demo_live.py

Prints a merchant-style operations report using the same tools an Agent
Studio agent would call over MCP.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from connector import tools  # noqa: E402
from connector.config import Config  # noqa: E402
from connector.woocommerce_client import WooCommerceClient  # noqa: E402


def main() -> None:
    cfg = Config.from_env()
    cfg.validate()
    client = WooCommerceClient(cfg)

    print("== Store health ==")
    print(json.dumps(tools.health_check(client), indent=2))

    print("\n== Pending / failed payments ==")
    for status in ("pending", "failed"):
        out = tools.list_orders(client, status=status, per_page=20)
        print(f"  {status}: {out['pagination']['total']} order(s)")
        for o in out["orders"][:5]:
            print(f"    #{o['number']}  {o['currency']} {o['total']}  {o['customer_name']}")

    print("\n== Recent orders ==")
    out = tools.list_orders(client, per_page=10)
    for o in out["orders"]:
        print(f"    #{o['number']}  {o['status']:<11} {o['total']}  {o['payment_method']}")

    print("\n== Low stock (<= 5) ==")
    inv = tools.list_inventory(client, low_stock_threshold=5)
    for p in inv["low_stock"]:
        print(f"    {p['name']:<32} qty={p['stock_quantity']}  sku={p['sku']}")
    print(f"    ({inv['count']} of {inv['scanned']} scanned)")

    print("\n== Product lookup by SKU ==")
    res = tools.search_products(client, sku="AUD-002")
    if res["products"]:
        p = res["products"][0]
        print(f"    {p['name']}  price={p['price']}  stock={p['stock_status']} ({p['stock_quantity']})")


if __name__ == "__main__":
    main()
