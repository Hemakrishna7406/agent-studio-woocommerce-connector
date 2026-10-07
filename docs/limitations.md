# Limitations, assumptions, and the long-term fix

Honest accounting of where this connector stops and what the right production
answer is. The assignment explicitly asks for limitations, so this is a
first-class document, not an appendix.

## Assumptions

1. The store is reachable over **HTTPS** and exposes the standard
   `/wp-json/wc/v3` REST API (any reasonably current WooCommerce).
2. The merchant has issued a **Read** API key to a dedicated user.
3. The store is **single-tenant per connector instance** — one store per
   deployment, configured by env vars.
4. Order/product/customer ids are stable and unique within a store.

## Limitations

### 1. Request-driven, not event-driven
The connector reads on demand. It does not know about a new order until the
agent asks. For "tell me when X happens" workflows, reads alone are the wrong
primitive.

### 2. Deep pagination does not scale
WooCommerce paginates with `?page=N`, which the database resolves with an
`OFFSET`. At high page numbers this is O(offset) and gets slow, and it can
skip or duplicate rows if the underlying data changes mid-scan. `per_page` is
capped at 100.

### 3. Rate limits are host-dependent
WooCommerce itself does not publish rate-limit headers. Real limits come from
the host, CDN or WAF, and can change without notice. We handle `429`/`5xx`
with `Retry-After` + exponential backoff and jitter, plus a client-side token
bucket — but we cannot guarantee the ceiling of an unknown host.

### 4. No incremental sync or caching
Every call hits the store. Repeated agent questions re-fetch the same data.

### 5. Read-only
Writes, refunds, fulfilment and status changes are out of scope.

### 6. PII handling is delegated
The connector returns customer name/email because the store's own API does.
Masking or field-level policy is left to the agent host / deployment, not
enforced here.

### 7. Search is store-side, not semantic
`search_products` uses WooCommerce's own text search. It is keyword-based, not
semantic, and its relevance ordering is the store's, not ours.

## The long-term fix

The limitations above are all symptoms of talking to the transactional store
directly. The durable architecture is:

1. **Incremental sync into a read replica / search index.**
   Use the `modified_after` filter and WooCommerce **webhooks** to keep a
   local Postgres/OpenSearch copy fresh. Then agent queries hit an index, not
   the store — killing limitation #1 and #2 at once.

2. **Cursor pagination on the index.**
   Replace offset paging with keyset/cursor pagination so deep reads stay
   O(log n) and are stable under concurrent writes.

3. **A per-store budget + queue.**
   Track the host's observed rate limit, drive reads through a queue with
   adaptive concurrency, and degrade gracefully rather than retry-storm.

4. **Caching with TTLs.**
   Cache product/category data (slow-changing) aggressively; cache orders with
   short TTLs invalidated by webhooks.

5. **A policy layer for PII.**
   Field-level access rules and redaction at the connector boundary, so the
   agent never receives data it isn't entitled to.

6. **Write tools behind explicit, audited approval.**
   If the merchant needs agent-driven actions, add them as separate tools with
   human-in-the-loop confirmation and an audit log — never bolted onto the
   read path.

This is exactly the "scalable long-term search primitives" the brief asks
about: today's connector is the correct, safe v1; the index-backed sync is the
v2 that removes the ceiling.
