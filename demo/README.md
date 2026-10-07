# Demo guide

Three ways to see the connector work, easiest first.

## 1. Offline (no setup, no network, no credentials) — start here

```bash
python demo/demo_offline.py
```

Starts a mock WooCommerce store in-process, points the real connector at it,
and runs `health_check`, `list_orders`, `search_products` and `list_inventory`.
It also injects a single `429` on the second request so you can watch the
retry logic work.

## 2. Live (real local WooCommerce via Docker)

```bash
cd demo
bash setup_store.sh       # WordPress + WooCommerce on http://localhost:8080
# create a Read/Write API key in wp-admin, then:
export WC_STORE_URL=http://localhost:8080
export WC_CONSUMER_KEY=ck_...
export WC_CONSUMER_SECRET=cs_...
python seed_data.py       # sample products + orders
python demo_live.py       # merchant-style operations report
```

## 3. As an MCP server (what Agent Studio would connect to)

```bash
python -m mcp_server.server                              # stdio
MCP_TRANSPORT=streamable-http python -m mcp_server.server # HTTP
```

The tools and their schemas are documented in `../docs/mcp-tool-spec.md`.
