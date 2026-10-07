# Demo output (captured)

Actual output of `python demo/demo_offline.py` — the zero-setup end-to-end
demo. It starts a mock WooCommerce store in-process and drives the real
connector against it. No Docker, no credentials, no network.

```text
====================================================================
Agent Studio — WooCommerce connector · offline end-to-end demo
====================================================================

[1] health_check: {
  "ok": true,
  "store_url": "http://127.0.0.1:8899"
}

[2] list_orders(status='processing')
    #1001  processing  INR   999.00  Cust0 Demo
    #1004  processing  INR  1299.00  Cust3 Demo
    #1007  processing  INR  1599.00  Cust6 Demo
    pagination: {'page': 1, 'per_page': 50, 'total': 3, 'total_pages': 1}

[3] search_products(query='Product')
    7 products, first = Product 0 @ 199.00

[4] list_inventory(low_stock_threshold=5)
    LOW: Product 0    qty=1
    LOW: Product 2    qty=3
    LOW: Product 3    qty=0
    LOW: Product 5    qty=2
    count=4 scanned=7

Done. (Note: request #2 was a simulated 429 — the client retried automatically.)
```

Note what this proves end to end:

- **Auth** — the mock store rejects any request without the correct Basic auth.
- **Pagination metadata** — `total`/`total_pages` come from `X-WP-Total` /
  `X-WP-TotalPages`.
- **Filtering** — `status='processing'` returns only 3 of the 7 orders.
- **Normalisation** — raw payloads come back as small, stable dicts.
- **Rate-limit recovery** — request #2 was a simulated `429`; the client
  retried with backoff and the run completed without error.
