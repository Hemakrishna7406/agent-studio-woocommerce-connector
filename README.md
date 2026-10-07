# Agent Studio — WooCommerce Private Connector

A read-only **MCP connector** that lets an Agent Studio agent read **orders,
products, inventory and customers** from a WooCommerce store.

Built for the Razorpay *Forward-Deployed Engineer, Agent Studio* assignment
(Option 3: private connector for a merchant tool).

> **Try it in 10 seconds, no setup:**
> ```bash
> pip install -r requirements.txt
> python demo/demo_offline.py
> ```
> This spins up a mock WooCommerce store in-process and drives the real
> connector against it — auth, pagination, rate-limit retry and normalisation,
> all live, with no Docker and no credentials.

---

## Why WooCommerce

- **Self-hostable:** the whole demo runs locally via Docker — no vendor
  account, no approval wait, and no real credentials anywhere in the repo.
- **Razorpay-relevant:** orders, payments and inventory are exactly the
  merchant commerce data a Forward-Deployed Engineer works with.
- **Real API surface:** a genuine REST API with pagination, filtering, auth
  and host-level rate limits — so the connector exercises the hard parts
  honestly.

---

## What's in the box

```
agent-studio-woocommerce-connector/
├── connector/                 # the connector core (framework-agnostic)
│   ├── config.py              # env-driven config, secrets never hard-coded
│   ├── errors.py              # typed errors (Auth/NotFound/RateLimited/Upstream)
│   ├── rate_limiter.py        # token bucket + backoff-with-jitter
│   ├── models.py              # normalisers (raw WC payload -> small dicts)
│   ├── woocommerce_client.py  # auth, retry, pagination, search primitives
│   └── tools.py               # agent-facing read operations
├── mcp_server/server.py       # MCP server exposing the 7 tools
├── docs/
│   ├── auth.md                # the key authentication flow
│   ├── mcp-tool-spec.md       # full tool specification + schemas
│   ├── capabilities.md        # what the agent can and cannot do
│   ├── limitations.md         # limitations, assumptions, long-term fix
│   └── master-plan.md         # how this was planned and sequenced
├── demo/
│   ├── demo_offline.py        # ★ mock store + real connector (no setup)
│   ├── demo_live.py           # report against a real local store
│   ├── docker-compose.yml     # WordPress + MySQL + WooCommerce + wp-cli
│   ├── setup_store.sh         # one-command local store bring-up
│   └── seed_data.py           # sample products & orders
├── tests/                     # 8 unit tests (client + tools), no network
├── .github/workflows/ci.yml   # runs tests + offline demo on every push
├── deploy_to_github.sh        # one-command GitHub deploy
├── requirements.txt
├── LICENSE
└── .env.example
```

---

## Quickstart — real store (Docker)

```bash
cd demo
bash setup_store.sh                  # brings up WordPress + WooCommerce
# create a Read API key at http://localhost:8080/wp-admin
export WC_STORE_URL=http://localhost:8080
export WC_CONSUMER_KEY=ck_...
export WC_CONSUMER_SECRET=cs_...
python seed_data.py                  # sample products + orders
python demo_live.py                  # the connector in action
```

## Configuration

Copy `.env.example` to `.env`. All secrets are read from the environment —
**nothing is hard-coded and nothing secret is ever logged or returned.**

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `WC_STORE_URL` | yes | — | store base URL (HTTPS in production) |
| `WC_CONSUMER_KEY` | yes | — | `ck_...` REST API key |
| `WC_CONSUMER_SECRET` | yes | — | `cs_...` REST API secret |
| `WC_TIMEOUT` | no | 20 | per-request timeout (s) |
| `WC_MAX_RETRIES` | no | 4 | retries on 429/5xx |
| `WC_PER_PAGE` | no | 100 | page size (max 100) |
| `WC_RPS` | no | 5 | client-side request rate |
| `WC_VERIFY_SSL` | no | true | TLS verification |

## Run the MCP server

```bash
python -m mcp_server.server                                   # stdio (MCP hosts)
MCP_TRANSPORT=streamable-http python -m mcp_server.server      # HTTP
```

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

---

## Deploy to GitHub

The repo is ready to publish as-is. One command does it:

```bash
bash deploy_to_github.sh <your-github-username> agent-studio-woocommerce-connector --public
```

That initialises git, commits, creates the repo and pushes — using the GitHub
CLI (`gh`) if you have it, otherwise printing the exact `git push` command to
run. The included **GitHub Actions workflow** (`.github/workflows/ci.yml`) then
runs the test suite and the offline demo on every push, so your repo shows a
passing CI run — a strong signal to a reviewer.

No secrets are involved: `.env` is gitignored, and `.env.example` holds
placeholders only.

---

## Design decisions

**Authentication.** HTTP Basic (`ck`/`cs`) over **HTTPS**, never in the query
string. The key is issued with **Read** permission to a dedicated
least-privilege user, so a leak can only read — it cannot damage the store.
Full flow in [`docs/auth.md`](docs/auth.md).

**Pagination / search primitives.** A single `paginate()` generator follows the
store's `X-WP-TotalPages` header and streams lazily with an optional
`max_items` cap. `page()` returns a slice plus metadata. This is the
*scalable* primitive: callers bound their own cost, and deep-pagination limits
are called out honestly in [`docs/limitations.md`](docs/limitations.md) along
with the index-backed long-term fix.

**Rate-limit handling.** Two layers: a client-side **token bucket** so we
never hammer the store, and **exponential backoff with jitter** that honours
`Retry-After` on 429/5xx. Exhausted retries raise a typed `RateLimitedError`.

**Normalisation.** Raw WooCommerce objects are large; returning them would
blow up the agent's context and leak fields it shouldn't rely on. Every
resource is projected to a small, documented shape in `models.py`.

**Typed errors.** The agent gets `AuthError`, `NotFoundError`,
`RateLimitedError` or `UpstreamError` — and can reason about them — instead of
a raw stack trace.

**Read-only.** No tool mutates the store. Bounded blast radius by design.

---

## How this maps to the assignment brief

| Requirement | Where it's satisfied |
|---|---|
| Connector lets an agent read tickets/orders/inventory | `connector/tools.py`, `mcp_server/server.py` (orders, products, inventory, customers) |
| Working demo **or** key authentication flow | **Both:** `demo/demo_offline.py` (runs with zero setup) + `docs/auth.md` |
| Scalable long-term search primitives | `WooCommerceClient.paginate()/page()` + `docs/limitations.md` long-term fix |
| Rate-limit handling | `connector/rate_limiter.py`, retry logic in `woocommerce_client.py` |
| MCP tool specification or equivalent | `docs/mcp-tool-spec.md` |
| Short doc: what the agent can and cannot do | `docs/capabilities.md` |
| Setup steps, restrictions, assumptions, limitations | `README.md` + `docs/limitations.md` |
| No real customer data / secrets | `.env.example` placeholders only; `.gitignore` excludes `.env` |

## Submission checklist

- [ ] Push to a public repo (or share a Google Drive folder) — no `.env`, no keys.
- [ ] Confirm `python demo/demo_offline.py` runs clean from a fresh clone.
- [ ] Confirm `python -m pytest` is green.
- [ ] Confirm the GitHub Actions run is green (tests + offline demo).
- [ ] Add a 2-minute screen recording of the offline demo (optional, high impact).
- [ ] Paste the repo link into the form's *Assignment submission link* field.
