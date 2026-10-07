# Master plan — how to win this assignment

This is the plan behind the repo: what to build, in what order, and how to
spend 48 hours so the submission reads as "this person already does the job."

## 0. The evaluation lens (read this first)

The role is **Forward-Deployed Engineer, Agent Studio**. The team is hiring
for someone who can talk to a merchant, find the *real* problem, build the
solution, and measure impact — on-site in Bangalore, customer-facing. So they
are not grading a toy. They are asking: *would I put this person in front of a
merchant next week?*

That means the submission is judged on:

1. **Does it actually work?** A reviewer must be able to run it.
2. **Judgement.** Do you handle auth, rate limits, pagination, PII and failure
   modes like someone who has shipped production software?
3. **Communication.** Can you explain what it can and cannot do, clearly, to a
   non-engineer?
4. **Fit.** Does it look like Agent Studio / MCP work specifically?

Everything below is sequenced to maximise those four.

## 1. Choice & rationale

**Option 3 — private connector — WooCommerce.**

- Option 3 is the only one that *is* the day job (Agent Studio + MCP tools).
- WooCommerce can be run **entirely locally** (Docker + WordPress), so the
  demo needs no vendor account, no approval wait, and no real credentials —
  which also satisfies the "no secrets / no real customer data" rule cleanly.
- It exercises the genuinely hard parts: auth, pagination, rate limits,
  normalisation, typed errors.

Why not the others: Option 1 (reverse-engineer an API) is the easiest to
finish but least differentiating. Option 2 (voice agent) is high-reward but
the riskiest in 48h because telephony/provider setup eats the clock.

## 2. Architecture (one line)

Agent Studio agent → **MCP tools** → connector core (`tools` → `client` →
auth / rate-limit / pagination) → WooCommerce REST API.

The connector core is **framework-agnostic**; MCP is a thin adapter on top.
That separation is itself a signal of judgement — it means the connector could
be reused by a different agent runtime without a rewrite.

## 3. Workstreams

| # | Workstream | Output | Why it matters |
|---|---|---|---|
| W1 | Skeleton + config + errors | `connector/{config,errors}.py` | Secrets hygiene, typed failure |
| W2 | Client: auth + retry + rate limit | `woocommerce_client.py`, `rate_limiter.py` | The "senior engineer" signals |
| W3 | Pagination + search primitives | `paginate()/page()` | Explicitly required by the brief |
| W4 | Tools + MCP server | `tools.py`, `mcp_server/server.py` | The actual product |
| W5 | Demo (offline + live) | `demo/*` | Reviewer must see it work |
| W6 | Docs | `docs/*`, README | Communication is graded |
| W7 | Tests + packaging | `tests/*`, zip/repo | Proof, and easy to run |

## 4. 48-hour timeline

**Day 1 — build the thing (working end to end)**

- **H0–1:** Set up repo, `.env.example`, config, errors. Decide the tool
  (WooCommerce) and write the one-line architecture into the README.
- **H1–4:** Client core: Basic auth over HTTPS, token bucket, backoff +
  `Retry-After`, typed errors. This is the differentiator — don't rush it.
- **H4–6:** Pagination generator + page-with-metadata. Write the two client
  tests as you go.
- **H6–9:** Tools layer + normalisers (orders, products, inventory,
  customers).
- **H9–11:** MCP server exposing the tools; get `demo_offline.py` running
  against a mock store. **This is the checkpoint: it works.**
- **H11–13:** Docker compose + seed script; bring up a real local store and
  run `demo_live.py` against it.
- **H13–14:** Commit, push, sleep.

**Day 2 — make it land**

- **H0–2:** Write `docs/capabilities.md` and `docs/limitations.md` (the
  long-term-fix section is where you show real judgement).
- **H2–4:** Finish `docs/mcp-tool-spec.md` and `docs/auth.md`.
- **H4–6:** Record a 2-minute screen capture of `demo_offline.py` +
  `demo_live.py`. Polish the README.
- **H6–8:** Red-team yourself: what would a Razorpay engineer poke at? Add
  the test or note that closes each hole.
- **H8–10:** Buffer. Then fill in the form (see §6) and submit **before** the
  48h mark.

## 5. Quality bar (what "good" looks like here)

- A reviewer clones the repo and sees it work **within 10 seconds** — hence
  the zero-setup offline demo.
- No secrets anywhere; `.env.example` has obvious placeholders.
- Failures are *typed and explained*, not swallowed.
- The limitations doc names the ceiling **and** the fix — that is the
  Forward-Deployed Engineer mindset: ship the safe v1, know the v2.
- Read-only by design, least-privilege key: you thought about blast radius.

## 6. The form questions (prepare answers)

The form also grades your written answers — treat them as seriously as the code.

- **Experience (0–2 / 2+):** answer honestly.
- **An LLM/agent solution you built:** name it, the tools/data it used, where
  you put guardrails or human review, and *how you measured quality*. Use this
  very assignment as your example if it fits.
- **Strongest production language:** Python or TypeScript, with a concrete
  system and your specific contribution.
- **On-site in Bangalore + leading technical conversations:** a clear yes,
  with a one-line example of a time you led a technical conversation with a
  customer.
- **Submission link:** public repo or a Drive folder accessible to the hiring
  team. **No secrets, no real customer data.**

## 7. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Store setup (Docker) fails on the reviewer's machine | The offline demo needs no store at all |
| Rate-limit behaviour can't be shown | The offline demo simulates a 429 and shows the retry |
| "Does it do enough?" | 7 tools, auth flow, pagination, rate limiting, spec, capability doc — the full brief |
| Time overrun | Day 1 ends at "it works end to end"; Day 2 is docs + polish only |

## 8. Stretch goals (only if time remains)

- `streamable-http` transport shown in a short clip.
- A tiny "agent loop" script that picks a tool based on a question (no LLM
  needed) to show the tools compose.
- A GitHub Actions workflow running the tests on push — cheap, strong signal.
