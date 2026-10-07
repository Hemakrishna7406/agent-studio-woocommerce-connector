# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] — 2026-10-07

### Added
- Read-only WooCommerce client: Basic auth over HTTPS, token-bucket rate
  limiting, `Retry-After`-aware exponential backoff with jitter, and typed
  errors (`AuthError`, `NotFoundError`, `RateLimitedError`, `UpstreamError`).
- Pagination and search primitives: `paginate()` (follows `X-WP-TotalPages`,
  lazy, capped) and `page()` (single slice + metadata).
- Seven MCP tools: `health_check`, `list_orders`, `get_order`,
  `search_products`, `get_product`, `list_inventory`, `get_customer`.
- Normalisers that project raw WooCommerce payloads to small, stable dicts.
- Zero-setup offline end-to-end demo (mock store + real connector, with a
  simulated `429`).
- Docker demo: local WordPress + WooCommerce + seeding.
- Docs: auth flow, MCP tool spec, capabilities, limitations + long-term fix,
  architecture, merchant problem framing + impact metrics, webhooks v2 design,
  master plan.
- Test suite (unit + pagination/retry/error behaviour) and GitHub Actions CI.
