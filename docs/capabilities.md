# What the agent can and cannot do

This connector gives an Agent Studio agent **read-only** access to a
WooCommerce store. This document is the contract: it says exactly what the
agent may rely on, and what it must not attempt.

## The agent CAN

| Capability | Tool | Notes |
|---|---|---|
| Verify the connection before acting | `health_check` | never raises; returns `ok:false` with a reason |
| List / filter orders | `list_orders` | by status, date range, customer, free-text search |
| Retrieve one order | `get_order` | line items, status, totals |
| Search the catalogue | `search_products` | by text, SKU, category, stock status |
| Retrieve one product | `get_product` | price, stock, categories |
| Find low-stock items | `list_inventory` | products at/below a threshold |
| Retrieve a customer | `get_customer` | order count, lifetime spend |

Typical agent tasks this enables:
- "Which orders failed or are still pending payment this week?"
- "What's about to go out of stock?"
- "Show me everything a given customer has bought."
- "Is SKU-014 in stock, and at what price?"

## The agent CANNOT

| Not supported | Why |
|---|---|
| Create / update / delete orders, products or customers | The connector is read-only by design, and the API key is issued with **Read** permission. |
| Process refunds or payments | Out of scope; belongs to the payments platform, not a read connector. |
| Read tickets | That is a different tool (e.g. Freshdesk); this connector targets WooCommerce commerce data. |
| Access customers not exposed by the store | We only surface what the merchant's own REST API returns. |
| Bypass access controls | No scraping, no admin-only endpoints, no privilege escalation. |
| Read more than `per_page` (max 100) in one call | Deliberate bound; the agent paginates or the tool streams. |
| See data newer than the last successful call | The connector is request-driven, not a live stream (see limitations). |

## Data the agent sees

The tools return **normalised projections**, not raw WooCommerce payloads.
That keeps the agent's context small and predictable. Fields like internal
meta, nonces and admin flags are stripped. Customer email/name are returned
because they are already exposed by the store's REST API — but this is
merchant data and must be handled accordingly (see limitations on PII).

## Safety posture

- **Least privilege:** issue the key to a dedicated Read-only user.
- **No secrets in output:** the connector never returns keys or tokens.
- **Bounded blast radius:** read-only means a misbehaving agent cannot corrupt
  the merchant's store.
- **Typed failures:** the agent receives `AuthError` / `NotFoundError` /
  `RateLimitedError` / `UpstreamError` and can decide how to proceed.
